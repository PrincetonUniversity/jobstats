import base64
import csv
import datetime
import gzip
import json
import os
import subprocess
import sys
import syslog
import time
from typing import Dict
import requests
import config as c
if c.EXTERNAL_DB_CONFIG.get("enabled", False):
    from db_handler import JobstatsDBHandler
if not hasattr(c, "GPU_EXPORTER_JOBID"):
    c.GPU_EXPORTER_JOBID = False
if not hasattr(c, "GPU_METRICS"):
    c.GPU_METRICS = {}
if not hasattr(c, "GPU_METRICS_EXPORTER"):
    c.GPU_METRICS_EXPORTER = "None"


__version__ = "1.0.0"

# number of seconds between measurements
SAMPLING_PERIOD = c.SAMPLING_PERIOD

# conversion factors
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600

# for convenience
DEVNULL = open(os.devnull, 'w')
# next line produces unix times
os.environ['SLURM_TIME_FORMAT'] = "%s"

# class that gets and holds per job prometheus statistics
class Jobstats:
    slurm_version = None
    sluid_available = False

    # initialize basic job stats, can be called either with those stats
    # provided and if not it will fetch them
    def __init__(self,
                 jobid=None,
                 jobidraw=None,
                 sluid=None,
                 start=None,
                 end=None,
                 gpus=None,
                 cluster=None,
                 prom_server=None,
                 debug=False,
                 debug_syslog=False,
                 force_recalc=False,
                 batch_script=False,
                 json_or_base64=False):
        if self.slurm_version == None:
            self.slurm_version = subprocess.check_output(["sacct", "-V"], stderr=DEVNULL).decode("utf-8").split()[1]
            if int(self.slurm_version.split(".")[0]) > 25:
                self.sluid_available = True
        self.cluster = cluster
        self.prom_server = prom_server
        self.debug = debug
        self.debug_syslog = debug_syslog
        self.force_recalc = force_recalc
        self.batch_script = batch_script
        self.json_or_base64 = json_or_base64
        self.sp_node = {}
        # translate cluster name
        if self.cluster in c.CLUSTER_TRANS:
            self.cluster = c.CLUSTER_TRANS[self.cluster]
        if self.debug_syslog:
            syslog.openlog('jobstat[%s]' % jobid)
        if jobidraw is None:
            self.jobid = jobid
            if not self.__get_job_info():
                if self.state == "PENDING":
                    self.error("Failed to get details for job %s since it is a PENDING job." % jobid)
                else:
                    self.error("Failed to get details for job %s." % jobid)
        else:
            if jobid is None:
                jobid = jobidraw
            self.jobid = jobid
            self.jobidraw = jobidraw
            self.start = start
            self.end = end
            self.gpus = gpus
            self.data = None
            self.timelimitraw = None
        self.diff = self.end - self.start
        # translate cluster name
        #if self.cluster in c.CLUSTER_TRANS_INV:
        #    self.cluster = c.CLUSTER_TRANS_INV[self.cluster]
        self.debug_print("jobid=%s, " \
                         "jobidraw=%s, " \
                         "sluid=%s, " \
                         "start=%s, " \
                         "end=%s, " \
                         "gpus=%s, " \
                         "diff=%s, " \
                         "cluster=%s, " \
                         "data=%s, " \
                         "timelimitraw=%s" % (self.jobid,
                                              self.jobidraw,
                                              self.sluid,
                                              self.start,
                                              self.end,
                                              self.gpus,
                                              self.diff,
                                              self.cluster,
                                              self.data,
                                              self.timelimitraw))
        if self.data is not None and self.data.startswith('JS1:') and len(self.data) > 10:
            try:
                t = json.loads(gzip.decompress(base64.b64decode(self.data[4:])))
                self.sp_node = t["nodes"]
            except Exception as e:
                print("ERROR: %s" %e)
        if not self.sp_node and (self.diff >= 2 * SAMPLING_PERIOD):
            # call prometheus to get detailed statistics (if long enough)
            self.get_job_stats()
        if len(self.sp_node) == 0 and self.json_or_base64:
            return
        self.parse_stats()
        if self.batch_script:
            cmd = ["sacct", "-j", f"{self.jobid}", "-B"]
            self.job_script = subprocess.check_output(cmd, stderr=DEVNULL).decode("utf-8")

    def nodes(self):
        return self.sp_node

    def jobid(self):
        return self.jobidraw

    def diff(self):
        return self.diff

    def gpus(self):
        return self.gpus

    # report an error on stderr and fail
    def error(self, msg):
        sys.stderr.write("%s\n" % msg)
        if self.debug_syslog:
            syslog.syslog(msg)
        sys.exit(1)

    def debug_print(self, msg):
        if self.debug:
            print('DEBUG: %s' % msg)
        if self.debug_syslog:
            syslog.syslog(msg)

    # Get basic info from sacct and set instance variables
    def __get_job_info(self):
        fields = ["jobidraw",
                  "start",
                  "end",
                  "cluster",
                  "alloctres",
                  "admincomment",
                  "user",
                  "account",
                  "state",
                  "nnodes",
                  "ncpus",
                  "reqmem",
                  "qos",
                  "partition",
                  "timelimitraw",
                  "jobname"]
        if self.sluid_available:
            fields.insert(-1, "sluid")
        # jobname must be the last field to handle "|" chars later on
        assert fields[-1] == "jobname"
        fields = ",".join(fields)
        cmd = ["sacct", "-P", "-X", "-o", fields, "-j", self.jobid]
        if self.cluster:
            cmd += ["-M", self.cluster]
        self.start    = None
        self.end      = None
        self.jobidraw = None
        try:
            sacct_output = subprocess.check_output(cmd, stderr=DEVNULL).decode("utf-8").split('\n')
            for i in csv.DictReader(sacct_output, delimiter='|'):
                self.jobidraw     = i.get('JobIDRaw', None)
                self.sluid        = i.get('SLUID', None)
                self.start        = i.get('Start', None)
                self.end          = i.get('End', None)
                self.cluster      = i.get('Cluster', None)
                self.tres         = i.get('AllocTRES', None)
                if self.force_recalc:
                    self.data = None
                else:
                    # Try to get AdminComment from Slurm database first
                    self.data = i.get('AdminComment', None)
                    
                    # If no data found and external DB is enabled, try external DB
                    if (not self.data or self.data == '') and c.EXTERNAL_DB_CONFIG.get("enabled", False):
                        try:
                            db_handler = JobstatsDBHandler()
                            self.data = db_handler.get_jobstats(self.cluster, self.jobidraw)
                            if self.data:
                                msg = f"Retrieved job data from external database for job {self.jobidraw}"
                                self.debug_print(msg)
                        except Exception as e:
                            self.debug_print(f"Failed to retrieve from external database: {e}")
                            
                self.user         = i.get('User', None)
                self.account      = i.get('Account', None)
                self.state        = i.get('State', None)
                self.timelimitraw = i.get('TimelimitRaw', None)
                self.nnodes       = i.get('NNodes', None)
                self.ncpus        = i.get('NCPUS', None)
                self.reqmem       = i.get('ReqMem', None)
                self.qos          = i.get('QOS', None)
                self.partition    = i.get('Partition', None)
                self.jobname      = i.get('JobName', None)
                self.debug_print('jobidraw=%s, ' \
                                 'sluid=%s, ' \
                                 'start=%s, ' \
                                 'end=%s, ' \
                                 'cluster=%s, ' \
                                 'tres=%s, ' \
                                 'data=%s, ' \
                                 'user=%s, ' \
                                 'account=%s, ' \
                                 'state=%s, ' \
                                 'timelimit=%s, ' \
                                 'nodes=%s, ' \
                                 'ncpus=%s, ' \
                                 'reqmem=%s, ' \
                                 'qos=%s, ' \
                                 'partition=%s, ' \
                                 'jobname=%s' % (self.jobidraw,
                                                 self.sluid,
                                                 self.start,
                                                 self.end,
                                                 self.cluster,
                                                 self.tres,
                                                 self.data,
                                                 self.user,
                                                 self.account,
                                                 self.state,
                                                 self.timelimitraw,
                                                 self.nnodes,
                                                 self.ncpus,
                                                 self.reqmem,
                                                 self.qos,
                                                 self.partition,
                                                 self.jobname))
        except Exception:
            msg = (f"\nFailed to lookup job {self.jobid}. Make sure the cluster is correct by\n"
                   "specifying the -c option (e.g., $ jobstats 1234567 -c frontier).\n")
            self.error(msg)
 
        if self.jobidraw is None:
            if self.cluster:
                clstr = c.CLUSTER_TRANS.get(self.cluster, self.cluster)
                msg = f"Failed to lookup job {self.jobid} on {clstr}."
                self.error(msg)
            else:
                msg = (f"\nFailed to lookup job {self.jobid}. Make sure the cluster is correct by\n"
                       "specifying the -c option (e.g., $ jobstats 1234567 -c frontier).\n")
                self.error(msg)

        self.gpus = 0
        if self.tres is not None and 'gres/gpu=' in self.tres and 'gres/gpu=0,' not in self.tres:
            for part in self.tres.split(","):
                if "gres/gpu=" in part:
                    self.gpus = int(part.split("=")[-1])
 
        if self.timelimitraw.isnumeric():
            self.timelimitraw = int(self.timelimitraw)
        if "CANCEL" in self.state:
            self.state = "CANCELLED"
        if len(self.jobname) > c.MAX_JOBNAME_LEN:
            self.jobname = self.jobname[:c.MAX_JOBNAME_LEN] + "..."

        # currently running jobs will have Unknown as time
        if self.end == 'Unknown':
            self.end = time.time()
        else:
            if self.end.isnumeric():
                self.end = int(self.end)
            else:
                return False
        if self.start.isnumeric():
            self.start = int(self.start)
            return True
        else:
            return False

    # extract info out of what was returned
    # sp = hash indexed by node
    # d  = data returned from prometheus
    # n  = what name to give this data
    # {'metric': {'__name__': 'cgroup_memory_total_bytes',
    #             'cluster': 'stellar',
    #             'instance': 'stellar-m02n30:9306',
    #             'job': 'Stellar Nodes',
    #             'jobid': '50783'},
    #             'values': [[1629592582, '536870912000']]}
    # or
    # {'metric': {'cluster': 'stellar',
    #             'instance': 'stellar-m06n4:9306',
    #             'job': 'Stellar Nodes',
    #             'jobid': '50783'},
    #             'value': [1629592575, '190540828672']}
    def get_data_out(self, d, n):
        if 'data' in d:
            j = d['data']['result']
            for i in j:
                node = i['metric']['instance'].split(':')[0]
                minor = i['metric'].get('minor_number', None)
                if 'value' in i:
                    v = i['value'][1]
                if 'values' in i:
                    v = i['values'][0][0]
                # trim unneeded precision
                if '.' in v:
                    x = float(v)
                    if x >= 0.1:
                        v = round(x, 1)
                    else:
                        v = round(x, 3)
                else:
                    v = int(v)
                if node not in self.sp_node:
                    self.sp_node[node] = {}
                if minor is not None:
                    if n not in self.sp_node[node]:
                        self.sp_node[node][n] = {}
                    self.sp_node[node][n][minor] = v
                else:
                    self.sp_node[node][n] = v

    def get_data(self, where, query, query_sluid=False):
        # run a query against prometheus
        def __run_query(q, start=None, end=None, time=None, step=2*SAMPLING_PERIOD):
            params = { 'query': q, }
            if start:
                params['start'] = start
                params['end'] = end
                params['step'] = step
                qstr = 'query_range'
            else:
                qstr = 'query'
                if time:
                    params['time'] = time
            response = requests.get(f'{self.prom_server}/api/v1/{qstr}', params)
            return response.json()
        
        expanded_query = query.format(cluster=self.cluster, jobid=self.jobidraw, diff=int(self.diff))
        if query_sluid and self.sluid != None:
            expanded_query += " or " + query.format(cluster=self.cluster, jobid=self.sluid, diff=int(self.diff))
        self.debug_print("query=%s, time=%s" % (expanded_query, self.end))
        try:
            j = __run_query(expanded_query, time=self.end)
        except Exception as e:
            self.error("ERROR: Failed to query jobstats database, got error: %s:" % e)
        self.debug_print("query result=%s" % j)
        if j["status"] == 'success':
            self.get_data_out(j, where)
        elif j["status"] == 'error':
            self.error("ERROR: Failed to get run query %s with time %s, error: %s" % (expanded_query,
                                                                                      self.end,
                                                                                      j["error"]))
        else:
            self.error("ERROR: Unknown result when running query %s with time %s. Full output: %s" % (expanded_query,
                                                                                                      self.end,
                                                                                                      j))

    def gpu_metric_query_string(self, metric: str, op: str) -> str:
        """Generate the Prometheus query string for the given metric and operation."""
        if op not in ("avg_over_time", "max_over_time", "min_over_time", "stddev_over_time"):
            self.error(f"Operation {op} is not a supported Prometheus function.")
        metrics = {}
        if c.GPU_METRICS_EXPORTER == "NVML":
            metrics["duty_cycle"]              = "nvidia_gpu_duty_cycle"
            metrics["memory_used_bytes"]       = "nvidia_gpu_memory_used_bytes"
            metrics["memory_total_bytes"]      = "nvidia_gpu_memory_total_bytes"
            metrics["sm_util_percent"]         = "nvidia_gpu_sm_util_percent"
            metrics["sm_occupancy_percent"]    = "nvidia_gpu_sm_occupancy_percent"
            metrics["any_tensor_util_percent"] = "nvidia_gpu_any_tensor_util_percent"
            metrics["fp16_util_percent"]       = "nvidia_gpu_fp16_util_percent"
            metrics["fp32_util_percent"]       = "nvidia_gpu_fp32_util_percent"
            metrics["fp64_util_percent"]       = "nvidia_gpu_fp64_util_percent"
            metrics["integer_util"]            = "nvidia_gpu_integer_util"
            metrics["pcie_rx_per_sec"]         = "nvidia_gpu_pcie_rx_per_sec"
            metrics["pcie_tx_per_sec"]         = "nvidia_gpu_pcie_tx_per_sec"
            metrics["nvlink_total_rx_per_sec"] = "nvidia_gpu_nvlink_total_rx_per_sec"
            metrics["nvlink_total_tx_per_sec"] = "nvidia_gpu_nvlink_total_tx_per_sec"
            metrics["temperature_celsius"]     = "nvidia_gpu_temperature_celsius"
            metrics["power_usage_milliwatts"]  = "nvidia_gpu_power_usage_milliwatts"
        elif c.GPU_METRICS_EXPORTER == "DCGM":
            metrics["duty_cycle"]              = "DCGM_FI_DEV_GPU_UTIL"
            metrics["memory_used_MiB"]         = "DCGM_FI_DEV_FB_USED"
            metrics["memory_total_MiB"]        = "DCGM_FI_DEV_FB_TOTAL"
            metrics["sm_util_percent"]         = "DCGM_FI_PROF_SM_ACTIVE"
            metrics["sm_occupancy_percent"]    = "DCGM_FI_PROF_SM_OCCUPANCY"
            metrics["any_tensor_util_percent"] = "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE"
            metrics["fp16_util_percent"]       = "DCGM_FI_PROF_PIPE_FP16_ACTIVE"
            metrics["fp32_util_percent"]       = "DCGM_FI_PROF_PIPE_FP32_ACTIVE"
            metrics["fp64_util_percent"]       = "DCGM_FI_PROF_PIPE_FP64_ACTIVE"
            metrics["integer_util"]            = "DCGM_FI_PROF_PIPE_INT_ACTIVE"
            metrics["pcie_rx_per_sec"]         = "DCGM_FI_PROF_PCIE_RX_BYTES"
            metrics["pcie_tx_per_sec"]         = "DCGM_FI_PROF_PCIE_TX_BYTES"
            metrics["nvlink_total_rx_per_sec"] = "DCGM_FI_PROF_NVLINK_RX_BYTES"
            metrics["nvlink_total_tx_per_sec"] = "DCGM_FI_PROF_NVLINK_TX_BYTES"
            metrics["temperature_celsius"]     = "DCGM_FI_DEV_GPU_TEMP"
            metrics["power_usage_milliwatts"]  = "DCGM_FI_DEV_POWER_USAGE"
        if metric in metrics:
            metric_full = metrics[metric]
        else:
            self.error(f"{metric} is not valid for exporter {c.GPU_METRICS_EXPORTER}.")
        if c.GPU_EXPORTER_JOBID:
            return f"{op}({metric_full}" + "{{cluster='{cluster}', jobid='{jobid}'}}[{diff}s:])"
        return f"{op}(({metric_full}" + "{{cluster='{cluster}'}} and nvidia_gpu_jobId == {jobid})[{diff}s:])"

    def get_job_stats(self, *args):
        # query CPU and Memory utilization data
        if not args or "total_memory" in args:
            self.get_data('total_memory', "max_over_time(cgroup_memory_total_bytes{{cluster='{cluster}',jobid='{jobid}',step='',task=''}}[{diff}s])", True)
        if not args or "used_memory" in args:
            self.get_data('used_memory', "max_over_time(((cgroup_memory_rss_bytes{{cluster='{cluster}',jobid='{jobid}',step='',task=''}}+cgroup_memory_shmem_bytes{{cluster='{cluster}',jobid='{jobid}',step='',task=''}}) or 1*cgroup_memory_rss_bytes{{cluster='{cluster}',jobid='{jobid}',step='',task=''}})[{diff}s:])", True)
        if not args or "total_time" in args:
            self.get_data('total_time', "max_over_time(cgroup_cpu_total_seconds{{cluster='{cluster}',jobid='{jobid}',step='',task=''}}[{diff}s])", True)
        if not args or "cpus" in args:
            self.get_data('cpus', "max_over_time(cgroup_cpus{{cluster='{cluster}',jobid='{jobid}',step='',task=''}}[{diff}s])", True)

        # and now GPUs
        if self.gpus:
            if not args or "gpu_total_memory" in args:
                if c.GPU_EXPORTER_JOBID:
                    self.get_data('gpu_total_memory', "max_over_time(nvidia_gpu_memory_total_bytes{{cluster='{cluster}',jobid='{jobid}'}}[{diff}s:])")
                else:
                    self.get_data('gpu_total_memory', "max_over_time((nvidia_gpu_memory_total_bytes{{cluster='{cluster}'}} and nvidia_gpu_jobId == {jobid})[{diff}s:])")
            if not args or "gpu_used_memory" in args:
                if c.GPU_EXPORTER_JOBID:
                    self.get_data('gpu_used_memory', "max_over_time(nvidia_gpu_memory_used_bytes{{cluster='{cluster}',jobid='{jobid}'}}[{diff}s:])")
                else:
                    self.get_data('gpu_used_memory', "max_over_time((nvidia_gpu_memory_used_bytes{{cluster='{cluster}'}} and nvidia_gpu_jobId == {jobid})[{diff}s:])")
            if not args or "gpu_utilization" in args:
                if c.GPU_EXPORTER_JOBID:
                    self.get_data('gpu_utilization', "avg_over_time((nvidia_gpu_duty_cycle{{cluster='{cluster}',jobid='{jobid}'}} or (nvidia_gpu_graphics_util_percent{{cluster='{cluster}',jobid='{jobid}'}} * 100))[{diff}s:])")
                else:
                    self.get_data('gpu_utilization', "avg_over_time(((nvidia_gpu_duty_cycle{{cluster='{cluster}'}} or (nvidia_gpu_graphics_util_percent{{cluster='{cluster}'}} * 100)) and nvidia_gpu_jobId == {jobid})[{diff}s:])")

            # detailed GPU metrics
            if c.GPU_METRICS and c.GPU_METRICS_EXPORTER == "None":
                self.error('Must set exporter to "NVML" or "DCGM" when GPU_METRICS is not empty.')
            if not args or c.GPU_METRICS:
                for name, settings in c.GPU_METRICS.items():
                    metric = settings["metric"]
                    operation = settings["operation"]
                    write_to_db = settings["write_to_db"]
                    prom_query_str = self.gpu_metric_query_string(metric, operation)
                    if self.json_or_base64:
                        if write_to_db:
                            self.get_data(name, prom_query_str)
                    else:
                        self.get_data(name, prom_query_str)

    def parse_stats(self):
        sp_node = self.sp_node
        if len(sp_node) == 0:
            if self.diff < SAMPLING_PERIOD:
                cmd = ["seff", f"{self.jobid}"]
                try:
                    seff = subprocess.check_output(cmd, stderr=DEVNULL).decode("utf-8")
                except Exception as e:
                    self.error(f"No job statistics are available ({e}).")
                else:
                    print("\nRun time is very short so only providing seff output:\n")
                    print(seff)
                    self.error("")
            else:
                self.error(f"No data was found for job {self.jobid}. This is probably because it is too old\n"
                          + "or it expired from Jobstats database. If you are not running this command on the\n"
                          + "cluster where the job was run then use the -c option to specify the cluster.\n"
                          +f'If the run time was very short then try running "seff {self.jobid}".')

        # cpu utilization
        total = 0
        total_used = 0
        total_cores = 0
        self.cpu_util_error_code = 0
        self.cpu_util__node_used_alloc_cores = []
        for n, d in sp_node.items():
            if 'total_time' in d and 'cpus' in d:
                used  = d['total_time']
                cores = d['cpus']
                alloc = self.diff * cores
                total += alloc
                total_used += used
                total_cores += cores
                self.cpu_util__node_used_alloc_cores.append((n, used, alloc, cores))
            else:
                self.cpu_util_error_code = 1
                self.cpu_util__node_used_alloc_cores.append((n, None, None, None))
                break
        if self.cpu_util_error_code == 0:
            if total_used > total:
                self.cpu_util_error_code = 2
            if total == 0:
                self.cpu_util_error_code = 3
        self.cpu_util_total__used_alloc_cores = (total_used, total, total_cores)

        # cpu memory
        total = 0
        total_used = 0
        total_cores = 0
        self.cpu_mem_error_code = 0
        self.cpu_mem__node_used_alloc_cores = []
        for n, d in sp_node.items():
            if 'used_memory' in d and 'total_memory' in d and 'cpus' in d:
                used  = d['used_memory']
                alloc = d['total_memory']
                cores = d['cpus']
                total += alloc
                total_used += used
                total_cores += cores
                self.cpu_mem__node_used_alloc_cores.append((n, used, alloc, cores))
            else:
                self.cpu_mem_error_code = 1
                self.cpu_mem__node_used_alloc_cores.append((n, None, None, None))
                break
        if self.cpu_mem_error_code == 0:
            if total_used > total:
                self.cpu_mem_error_code = 2
            if total == 0:
                self.cpu_mem_error_code = 3
        self.cpu_mem_total__used_alloc_cores = (total_used, total, total_cores)

        if self.gpus:
            # gpu utilization
            overall = 0
            overall_gpu_count = 0
            self.gpu_util_error_code = 0
            self.gpu_util__node_util_index = []
            for n, d in sp_node.items():
                if 'gpu_utilization' in d:
                    gpus = sorted(d['gpu_utilization'].keys())
                    for g in gpus:
                        util = d['gpu_utilization'][g]
                        overall += util
                        overall_gpu_count += 1
                        self.gpu_util__node_util_index.append((n, util, g))
                else:
                    if self.is_mig_job():
                        self.gpu_util__node_util_index.append((n, None, "#"))
                    else:
                        self.gpu_util_error_code = 1
                        self.gpu_util__node_util_index.append((n, None, None))
                        break
            self.gpu_util_total__util_gpus = (overall, overall_gpu_count)

            class DetailedGpuMetric:

                """Class for individual detailed GPU metrics."""

                def __init__(self, name: str, settings: Dict[str, Dict], is_mig: bool) -> None:
                    self.name = name
                    self.metric       = settings["metric"]
                    self.operation    = settings["operation"]
                    self.show_overall = settings["show_overall"]
                    self.show_per_gpu = settings["show_per_gpu"]
                    self.write_to_db  = settings["write_to_db"]
                    self.long_name    = settings.get("long_name")
                    self.is_mig = is_mig
                    ms = ("sm", "fp16", "fp32", "fp64", "tensor", "integer", "occupancy")
                    self.is_percentage = any(m in self.metric for m in ms)
                    if self.is_percentage:
                        self.fac = 100
                    elif "power" in self.metric:
                        self.fac = 0.001
                    else:
                        self.fac = 1
                    # finally correct duty_cycle
                    if "duty" in self.metric:
                        self.is_percentage = True

                def parse(self, sp_node: dict) -> None:
                    overall = 0
                    overall_gpu_count = 0
                    self.error_code = 0
                    self.node_value_index = []
                    for n, d in sp_node.items():
                        if self.name in d:
                            gpus = sorted(d[self.name].keys())
                            for g in gpus:
                                value = self.fac * d[self.name][g]
                                overall += value
                                overall_gpu_count += 1
                                self.node_value_index.append((n, value, g))
                        else:
                            if self.is_mig:
                                self.node_value_index.append((n, None, "#"))
                            else:
                                self.error_code = 1
                                self.node_value_index.append((n, None, None))
                                break
                    self.total__value_gpus = (overall, overall_gpu_count)

                def __str__(self) -> str:
                    return (f"{self.name}, {self.metric}, {self.operation}, "
                            f"{self.node_value_index}, {self.error_code}")

            self.detailed_gpu_metrics = []
            for name, settings in c.GPU_METRICS.items():
                gm = DetailedGpuMetric(name, settings, self.is_mig_job())
                gm.parse(sp_node)
                self.detailed_gpu_metrics.append(gm)
 
            # gpu memory
            overall = 0
            overall_total = 0
            self.gpu_mem_error_code = 0
            self.gpu_mem__node_used_total_index = []
            for n, d in sp_node.items():
                if 'gpu_used_memory' in d and 'gpu_total_memory' in d:
                    gpus = sorted(d['gpu_total_memory'].keys())
                    for g in gpus:
                        used  = d['gpu_used_memory'][g]
                        total = d['gpu_total_memory'][g]
                        overall += used
                        overall_total += total
                        self.gpu_mem__node_used_total_index.append((n, used, total, g))
                else:
                    self.gpu_mem_error_code = 1
                    self.gpu_mem__node_used_total_index.append((n, None, None, None))
                    break
            if self.gpu_mem_error_code == 0:
                if overall > overall_total:
                    self.gpu_mem_error_code = 2
                if overall_total == 0:
                    self.gpu_mem_error_code = 3
            self.gpu_mem_total__used_alloc = (overall, overall_total)

    def __str__(self, compact=False):
        js_data = {'nodes': self.sp_node, 'total_time': self.diff, 'gpus': self.gpus}
        if compact:
            return json.dumps(js_data, separators=(',', ':'))
        else:
            return json.dumps(js_data, sort_keys=True, indent=4)

    def is_retained(self) -> bool:
        """Returns true if the job is expected to be found in the Prometheus
           database. Job data is typically purged after N days."""
        if self.end and isinstance(self.end, (float, int)) and self.end > 1_000_000_000:
            job_end = datetime.datetime.fromtimestamp(self.end)
            now = datetime.datetime.now()
            return job_end > now - datetime.timedelta(days=c.PROM_RETENTION_DAYS)
        return False

    def is_mig_job(self) -> bool:
        """Returns true if the job ran on a MIG node."""
        mig_nodes_1 = getattr(c, "MIG_NODES_1", [])
        mig_nodes_2 = getattr(c, "MIG_NODES_2", [])
        return any(node in mig_nodes_1 or node in mig_nodes_2
                   for node in self.sp_node)

    def report_job_json(self, encode):
        data = self.__str__(encode)
        if encode:
            if self.diff < 2 * SAMPLING_PERIOD:
                return 'Short'
            elif len(self.sp_node) == 0:
                return 'None'
            else:
                return base64.b64encode(gzip.compress(data.encode('ascii'))).decode('ascii')
        else:
            return data
