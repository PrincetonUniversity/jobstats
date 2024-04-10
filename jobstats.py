import argparse
import csv
import datetime
import os
import subprocess
import sys
import time
import math
import requests
import json
import base64
import gzip
import syslog
from textwrap import TextWrapper
import config as c

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
class JobStats:
    # initialize basic job stats, can be called either with those stats
    # provided and if not it will fetch them
    def __init__(self,
                 jobid=None,
                 jobidraw=None,
                 start=None,
                 end=None,
                 gpus=None,
                 cluster=None,
                 prom_server=None,
                 debug=False,
                 debug_syslog=False,
                 force_recalc=False,
                 simple=False,
                 color=("" ,"" ,"")):
        self.cluster = cluster
        self.prom_server = prom_server
        self.debug = debug
        self.debug_syslog = debug_syslog
        self.force_recalc = force_recalc
        self.simple = simple
        self.sp_node = {}
        self.txt_bold   = color[0]
        self.txt_red    = color[1]
        self.txt_normal = color[2]
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
        if self.cluster in c.CLUSTER_TRANS_INV:
            self.cluster = c.CLUSTER_TRANS_INV[self.cluster]
        self.debug_print("jobid=%s, jobidraw=%s, start=%s, end=%s, gpus=%s, diff=%s, cluster=%s, data=%s, timelimitraw=%s" % 
            (self.jobid,self.jobidraw,self.start,self.end,self.gpus,self.diff,self.cluster,self.data,self.timelimitraw))
        if self.data is not None and self.data.startswith('JS1:') and len(self.data) > 10:
            try:
                t = json.loads(gzip.decompress(base64.b64decode(self.data[4:])))
                self.sp_node = t["nodes"]
            except Exception as e:
                print("ERROR: %s" %e)
        if not self.sp_node:
            # call prometheus to get detailed statistics (if long enough)
            if self.diff >= 2 * SAMPLING_PERIOD:
                self.get_job_stats()

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
        if __name__ == "__main__":
            sys.stderr.write("%s\n" % msg)
            if self.debug_syslog:
                syslog.syslog(msg)
            sys.exit(1)
        else:
            raise Exception(msg)

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
                  "reqtres",
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
            for i in csv.DictReader(subprocess.check_output(cmd,stderr=DEVNULL).decode("utf-8").split('\n'), delimiter='|'):
                self.jobidraw     = i.get('JobIDRaw', None)
                self.start        = i.get('Start', None)
                self.end          = i.get('End', None)
                self.cluster      = i.get('Cluster', None)
                self.tres         = i.get('ReqTRES', None)
                if self.force_recalc:
                    self.data     = None
                else:
                    self.data     = i.get('AdminComment', None)
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
                self.debug_print('jobidraw=%s, start=%s, end=%s, cluster=%s, tres=%s, data=%s, user=%s, account=%s, state=%s, timelimit=%s, nodes=%s, ncpus=%s, reqmem=%s, qos=%s, partition=%s, jobname=%s' % (self.jobidraw, self.start, self.end, self.cluster, self.tres, self.data, self.user, self.account, self.state, self.timelimitraw, self.nnodes, self.ncpus, self.reqmem, self.qos, self.partition, self.jobname))
        except Exception:
            self.error("Failed to lookup jobid %s" % self.jobid)
 
        if self.jobidraw == None:
            if self.cluster:
                clstr = c.CLUSTER_TRANS[self.cluster] if self.cluster in c.CLUSTER_TRANS else self.cluster
                self.error(f"Failed to lookup jobid %s on {clstr}. Make sure you specified the correct cluster." % self.jobid)
            else:
                self.error("Failed to lookup jobid %s." % self.jobid)

        self.gpus = 0
        if self.tres != None and 'gres/gpu=' in self.tres and 'gres/gpu=0,' not in self.tres:
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
    #{'metric': {'__name__': 'cgroup_memory_total_bytes', 'cluster': 'stellar', 'instance': 'stellar-m02n30:9306', 'job': 'Stellar Nodes', 'jobid': '50783'}, 'values': [[1629592582, '536870912000']]}
    # or
    #{'metric': {'cluster': 'stellar', 'instance': 'stellar-m06n4:9306', 'job': 'Stellar Nodes', 'jobid': '50783'}, 'value': [1629592575, '190540828672']}
    def get_data_out(self, d, n):
        if 'data' in d:
            j = d['data']['result']
            for i in j:
                node=i['metric']['instance'].split(':')[0]
                minor = i['metric'].get('minor_number', None)
                if 'value' in i:
                    v=i['value'][1]
                if 'values' in i:
                    v=i['values'][0][0]
                # trim unneeded precision
                if '.' in v:
                    v = round(float(v), 1)
                else:
                    v = int(v)
                if node not in self.sp_node:
                    self.sp_node[node] = {}
                if minor != None:
                    if n not in self.sp_node[node]:
                        self.sp_node[node][n] = {}
                    self.sp_node[node][n][minor] = v
                else:
                    self.sp_node[node][n] = v

    def get_data(self, where, query):
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
            response = requests.get('{0}/api/v1/{1}'.format(self.prom_server, qstr), params)
            return response.json()
        
        expanded_query = query%(self.cluster, self.jobidraw, self.diff)
        self.debug_print("query=%s, time=%s" %(expanded_query,self.end))
        try:
            j = __run_query(expanded_query, time=self.end)
        except Exception as e:
            self.error("ERROR: Failed to query jobstats database, got error: %s:" % e)
        self.debug_print("query result=%s" % j)
        if j["status"] == 'success':
            self.get_data_out(j, where)
        elif j["status"] == 'error':
            self.error("ERROR: Failed to get run query %s with time %s, error: %s" % (expanded_query, self.end, j["error"]))
        else:
            self.error("ERROR: Unknown result when running query %s with time %s, full output: %s" %(expanded_query, self.end, j))

    def get_job_stats(self):
        # query CPU and Memory utilization data
        self.get_data('total_memory', "max_over_time(cgroup_memory_total_bytes{cluster='%s',jobid='%s',step='',task=''}[%ds])")
        self.get_data('used_memory', "max_over_time(cgroup_memory_rss_bytes{cluster='%s',jobid='%s',step='',task=''}[%ds])")
        self.get_data('total_time', "max_over_time(cgroup_cpu_total_seconds{cluster='%s',jobid='%s',step='',task=''}[%ds])")
        self.get_data('cpus', "max_over_time(cgroup_cpus{cluster='%s',jobid='%s',step='',task=''}[%ds])")

        # and now GPUs
        if self.gpus:
            self.get_data('gpu_total_memory', "max_over_time((nvidia_gpu_memory_total_bytes{cluster='%s'} and nvidia_gpu_jobId == %s)[%ds:])")
            self.get_data('gpu_used_memory', "max_over_time((nvidia_gpu_memory_used_bytes{cluster='%s'} and nvidia_gpu_jobId == %s)[%ds:])")
            self.get_data('gpu_utilization', "avg_over_time((nvidia_gpu_duty_cycle{cluster='%s'} and nvidia_gpu_jobId == %s)[%ds:])")

    def human_bytes(self, size, decimal_places=1):
        size=float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f}{unit}"

    def human_seconds(self, seconds):
        hour = seconds // 3600
        if hour >= 24:
            days = "%d-" % (hour // 24)
            hour %= 24
            hour = days + ("%02d:" % hour)
        else:
            if hour > 0:
                hour = "%02d:" % hour
            else:
                hour = '00:'
        seconds = seconds % (24 * 3600)
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return "%s%02d:%02d" % (hour, minutes, seconds)

    def human_datetime(self, x):
       return datetime.datetime.fromtimestamp(x).strftime("%a %b %-d, %Y at %-I:%M %p")

    @staticmethod
    def rounded_memory_with_safety(mem_used: float) -> int:
        """Return a rounded version of the suggested memory including 20% safety."""
        mem_with_safety = math.ceil(1.2 * mem_used)
        if mem_with_safety > 1000:
            mem_suggested = round(mem_with_safety, -2)
            if mem_suggested - mem_with_safety < 0: mem_suggested += 100
        elif mem_with_safety > 100:
            mem_suggested = round(mem_with_safety, -1)
            if mem_suggested - mem_with_safety < 0: mem_suggested += 10
        elif mem_with_safety > 30:
            mem_suggested = round(mem_with_safety, -1)
            if mem_suggested - mem_with_safety < 0: mem_suggested += 5
        else:
            return max(1, mem_with_safety)
        return mem_suggested

    def simple_output(self):
        gutter = "  "
        # cpu time utilization
        print(f"{gutter}CPU utilization per node (CPU time used/run time)") 
        for node, used, alloc, cores in self.cpu_util__node_used_alloc_cores:
            msg = ""
            if used == 0: msg = f" {self.txt_bold}{self.txt_red}<--- CPU node was not used{self.txt_normal}"
            print(f"{gutter}    {node}: {self.human_seconds(used)}/{self.human_seconds(alloc)} (efficiency={100 * used / alloc:.1f}%){msg}")
        used, alloc, _ = self.cpu_util_total__used_alloc_cores
        if self.nnodes != "1":
            print(f"{gutter}Total used/runtime: {self.human_seconds(used)}/{self.human_seconds(alloc)}, efficiency={100 * used / alloc:.1f}%")
        # cpu memory usage
        print(f"\n{gutter}CPU memory usage per node - used/allocated")
        for node, used, alloc, cores in self.cpu_mem__node_used_alloc_cores:
            print(f"{gutter}    {node}: {self.human_bytes(used)}/{self.human_bytes(alloc)} ", end="")
            print(f"({self.human_bytes(used*1.0/cores)}/{self.human_bytes(alloc*1.0/cores)} per core of {cores})")
        total_used, total, total_cores = self.cpu_mem_total__used_alloc_cores
        if self.nnodes != "1":
            print(f"{gutter}Total used/allocated: {self.human_bytes(total_used)}/{self.human_bytes(total)} ", end="")
            print(f"({self.human_bytes(total_used*1.0/total_cores)}/{self.human_bytes(total*1.0/total_cores)} per core of {total_cores})")
        if self.gpus:
            # gpu utilization
            print(f"\n{gutter}GPU utilization per node")
            if self.partition == "mig":
                print(f"{gutter}    {node} (GPU): GPU utilization is unknown for MIG jobs")
            else:
                for node, util, gpu_index in self.gpu_util__node_util_index:
                    msg = ""
                    if util == 0: msg = f" {self.txt_bold}{self.txt_red}<--- GPU was not used{self.txt_normal}"
                    print(f"{gutter}    {node} (GPU {gpu_index}): {util}%{msg}")
            # gpu memory usage
            print(f"\n{gutter}GPU memory usage per node - maximum used/total")
            for node, used, total, gpu_index in self.gpu_mem__node_used_total_index:
                print(f"{gutter}    {node} (GPU {gpu_index}): {self.human_bytes(used)}/{self.human_bytes(total)} ({100.0*used/total:.1f}%)")

    def format_note(self, *items, style="normal", indent_width=4, bullet="*") -> str:
        """Combine the pieces of the note and apply formatting."""
        indent = " " * indent_width
        first_indent = [" " for _ in range(indent_width)]
        if len(first_indent) >= 2:
            first_indent[-2] = bullet
        first_indent = "".join(first_indent)
        wrapper = TextWrapper(width=78, subsequent_indent=indent, break_on_hyphens=False)
        # combine the parts of the note
        note = ""
        starts = ("http", "ftp", "$ ", "#SBATCH")
        for i, item in enumerate(items):
            if i == 0:
                wrapper.initial_indent = first_indent
                note += wrapper.fill(item)
            elif any([item.startswith(start) for start in starts]):
                note += f"\n{indent}  {item}\n"
            elif item == "\n":
                note += item
            else:
                wrapper.initial_indent = indent
                note += wrapper.fill(item)
        # apply styling
        if style == "bold":
            styling = self.txt_bold
        elif style == "bold-red":
            styling = f"{self.txt_bold}{self.txt_red}"
        else:
            styling = ""
        # add newline(s) to the end of the note
        if any([items[-1].startswith(start) for start in starts]):
            newlines = "\n"
        else:
            newlines = "\n\n"
        return f"{styling}{note}{self.txt_normal}{newlines}"

    def job_notes(self):
        s = ""
        # compute several quantities which can then referenced in notes
        total_used, total, total_cores = self.cpu_mem_total__used_alloc_cores
        cores_per_node = int(self.ncpus) / int(self.nnodes)
        gb_per_core_used = total_used / total_cores / 1024**3 if total_cores != 0 else 0
        gb_per_node_used = total_used / int(self.nnodes) / 1024**3 if int(self.nnodes) != 0 else 0
        # zero GPU/CPU utilization
        num_unused_gpus = sum([util == 0 for _, util, _ in self.gpu_util__node_util_index]) if self.gpus else 0
        zero_gpu = False  # TODO
        zero_cpu = False  # TODO
        gpu_show = True   # TODO
        # low GPU utilization
        interactive_job = "sys/dashboard/sys/" in self.jobname or self.jobname == "interactive"
        # low cpu utilization
        somewhat = " " if self.cpu_efficiency < c.CPU_UTIL_RED else " somewhat "
        ceff = self.cpu_efficiency if self.cpu_efficiency > 0 else "less than 1"
        # next three lines needed for serial code using multiple CPU-cores note
        eff_if_serial = 100 / int(self.ncpus) if self.ncpus != "0" else -1
        serial_ratio = self.cpu_efficiency / eff_if_serial
        approx = " approximately " if self.cpu_efficiency != round(eff_if_serial) else " "
        # next four lines needed for excess CPU memory note
        cpu_memory_utilization = round(100 * total_used / total) if total != 0 else 0
        gb_per_core = total / total_cores / 1024**3 if total_cores != 0 else 0
        opening = f"only used {cpu_memory_utilization}%" if cpu_memory_utilization >= 1 \
                                                         else "used less than 1%"
        cpn = c.CORES_PER_NODE[self.cluster] if self.cluster in c.CORES_PER_NODE else 0
        mpc = c.DEFAULT_MEM_PER_CORE[self.cluster] if self.cluster in c.DEFAULT_MEM_PER_CORE else 0
        # loop over notes
        for condition, note, style in c.NOTES:
            if eval(condition):
                if isinstance(note, str):
                    note = (note,)
                note_eval = []
                for item in note:
                    # check for and evaluate f-strings
                    if ('f"' in item or "f'" in item) and "{" in item and "}" in item:
                        note_eval.append(eval(item))
                    else:
                        note_eval.append(item)
                s += self.format_note(*note_eval, style=style)
        return s

    def cpu_memory_formatted(self, with_label=True):
        total = self.reqmem.replace("000M", "G").replace("000G", "T").replace(".50G", ".5G").replace(".50T", ".5T")
        if (int(self.ncpus) == 1 or all([X not in total for X in ("K", "M", "G", "T")])) and with_label:
            return f'     CPU Memory: {total.replace("M", "MB").replace("G", "GB").replace("T", "TB")}'
        if total.endswith("K"):
            bytes_ = float(total.replace("K", "")) * 1e3
        elif total.endswith("M"):
            bytes_ = float(total.replace("M", "")) * 1e6
        elif total.endswith("G"):
            bytes_ = float(total.replace("G", "")) * 1e9
        elif total.endswith("T"):
            bytes_ = float(total.replace("T", "")) * 1e12
        else:
            return total
        bytes_per_core = bytes_ / int(self.ncpus)
        for unit in ['B','KB', 'MB', 'GB', 'TB']:
            if bytes_per_core < 1000:
                break
            bytes_per_core /= 1000
        bpc = f"{bytes_per_core:.1f}"
        bpc = bpc.replace(".0", "")
        ttl = total.replace("M", "MB").replace("G", "GB").replace("T", "TB")
        if with_label:
            return f'     CPU Memory: {ttl} ({bpc}{unit} per CPU-core)'
        else:
            return ttl

    def time_limit_formatted(self):
        self.time_eff_violation = False
        clr = self.txt_normal
        if self.state == "COMPLETED" and self.timelimitraw > 0:
            self.time_efficiency = round(100 * self.diff / (SECONDS_PER_MINUTE * self.timelimitraw))
            if self.time_efficiency > 100:
                self.time_efficiency = 100
            if self.time_efficiency < c.TIME_EFFICIENCY_BLACK and self.diff > 3 * c.MIN_RUNTIME_SECONDS:
                self.time_eff_violation = True
            if self.time_efficiency < c.TIME_EFFICIENCY_RED and self.time_eff_violation:
                clr = f"{self.txt_bold}{self.txt_red}"
        return f"     Time Limit: {clr}{self.human_seconds(SECONDS_PER_MINUTE * self.timelimitraw)}{self.txt_normal}"

    def enhanced_output(self):
        print("")
        print(80 * "=")
        print("                              Slurm Job Statistics")
        print(80 * "=")
        print(f"         Job ID: {self.txt_bold}{self.jobid}{self.txt_normal}")
        print(f"  NetID/Account: {self.user}/{self.account}")
        print(f"       Job Name: {self.jobname}")
        if self.state in ("OUT_OF_MEMORY", "TIMEOUT"):
            print(f"          State: {self.txt_bold}{self.txt_red}{self.state}{self.txt_normal}")
        else:
            print(f"          State: {self.state}")
        print(f"          Nodes: {self.nnodes}")
        print(f"      CPU Cores: {self.ncpus}")
        print(self.cpu_memory_formatted())
        if self.gpus:
            print(f"           GPUs: {self.gpus}")
        print(f"  QOS/Partition: {self.qos}/{self.partition}")
        print(f"        Cluster: {self.cluster}")
        print(f"     Start Time: {self.human_datetime(self.start)}")
        if self.state == "RUNNING":
            print(f"       Run Time: {self.human_seconds(self.diff)} (in progress)")
        else:
            print(f"       Run Time: {self.human_seconds(self.diff)}")
        print(self.time_limit_formatted())
        print("")
        print(f"                              {self.txt_bold}Overall Utilization{self.txt_normal}")
        print(80 * "=")

        def draw_meter(x, hardware, util=False):
            bars = x // 2
            if bars < 0:  bars = 0
            if bars > 50: bars = 50
            text = f"{x}%"
            spaces = 50 - bars - len(text)
            if bars + len(text) > 50:
                bars = 50 - len(text)
                spaces = 0
            clr1 = ""
            clr2 = ""
            if (x < c.CPU_UTIL_RED and hardware == "cpu" and util and (not self.gpus)) or \
               (x < c.GPU_UTIL_RED and hardware == "gpu" and util):
                clr1 = f"{self.txt_red}"
                clr2 = f"{self.txt_bold}{self.txt_red}"
            return f"{self.txt_bold}[{self.txt_normal}" + clr1 + bars * "|" + spaces * " " + clr2 + \
                   text + f"{self.txt_normal}{self.txt_bold}]{self.txt_normal}"

        # overall cpu time utilization
        total_used, total, total_cores = self.cpu_util_total__used_alloc_cores
        self.cpu_efficiency = round(100 * total_used / total) if total != 0 else 0
        print("  CPU utilization  " + draw_meter(self.cpu_efficiency, "cpu", util=True))
        # overall cpu memory utilization
        total_used, total, total_cores = self.cpu_mem_total__used_alloc_cores
        cpu_memory_efficiency = round(100 * total_used / total) if total != 0 else 0
        print("  CPU memory usage " + draw_meter(cpu_memory_efficiency, "cpu"))
        if self.gpus:
            # overall gpu utilization
            overall, overall_gpu_count = self.gpu_util_total__util_gpus
            self.gpu_utilization = overall / overall_gpu_count
            if self.partition == "mig":
                unknown = f"  GPU utilization  {self.txt_bold}[{self.txt_normal}" \
                          f"     GPU utilization is unknown for MIG jobs      " \
                          f"{self.txt_normal}{self.txt_bold}]{self.txt_normal}"
                print(unknown)
            else:
                print("  GPU utilization  " + draw_meter(round(self.gpu_utilization), "gpu", util=True))
            # overall gpu memory usage
            overall, overall_total = self.gpu_mem_total__used_alloc
            gpu_memory_usage = round(100 * overall / overall_total)
            print("  GPU memory usage " + draw_meter(gpu_memory_usage, "gpu"))
        print()
        print(f"                              {self.txt_bold}Detailed Utilization{self.txt_normal}")
        print(80 * "=")
        self.simple_output()
        print()
        notes = self.job_notes()
        if notes:
            print(f"                                     {self.txt_bold}Notes{self.txt_normal}")
            print(80 * "=")
            print(notes)


    def report_job(self):
        sp_node = self.sp_node

        if len(sp_node) == 0:
            if self.diff < SAMPLING_PERIOD:
                cmd = ["seff",  f"{self.jobid}"]
                try:
                    seff = subprocess.check_output(cmd, stderr=DEVNULL).decode("utf-8")
                except:
                    self.error("No job statistics are available.")
                else:
                  print("\nRun time is very short so only providing seff output:\n")
                  print(seff)
                  self.error("")
            else:
                self.error(f"No stats found for job {self.jobid}, either because it is too old or because\n"
                          + "it expired from jobstats database. If you are not running this command on the\n"
                          + "cluster where the job was run then use the -c option to specify the cluster.\n"
                          +f'If the run time was very short then try running "seff {self.jobid}".')

        # cpu utilization
        total = 0
        total_used = 0
        total_cores = 0
        self.cpu_util__node_used_alloc_cores = []
        for n in sp_node:
            used = sp_node[n]['total_time']
            cores = sp_node[n]['cpus']
            alloc = self.diff * cores
            total += alloc
            total_used += used
            total_cores += cores
            self.cpu_util__node_used_alloc_cores.append((n, used, alloc, cores))
        self.cpu_util_total__used_alloc_cores = (total_used, total, total_cores)

        # cpu memory
        total = 0
        total_used = 0
        total_cores = 0
        self.cpu_mem__node_used_alloc_cores = []
        for n in sp_node:
            used = sp_node[n]['used_memory']
            alloc = sp_node[n]['total_memory']
            cores = sp_node[n]['cpus']
            total += alloc
            total_used += used
            total_cores += cores
            self.cpu_mem__node_used_alloc_cores.append((n, used, alloc, cores))
        self.cpu_mem_total__used_alloc_cores = (total_used, total, total_cores)

        if self.gpus:
            # gpu utilization
            overall = 0
            overall_gpu_count = 0
            self.gpu_util__node_util_index = []
            key_found = True
            for n in sp_node:
                d = sp_node[n]
                if 'gpu_utilization' in d:
                    gpus = list(d['gpu_utilization'].keys())
                    gpus.sort()
                    for g in gpus:
                        util = d['gpu_utilization'][g]
                        overall += util
                        overall_gpu_count += 1
                        self.gpu_util__node_util_index.append((n, util, g))
                else:
                    # this branch deals with mig
                    key_found = False
                    self.gpu_util__node_util_index.append((n, 50, "0"))
            if key_found:
                self.gpu_util_total__util_gpus = (overall, overall_gpu_count)
            else:
                # this branch deals with mig
                self.gpu_util_total__util_gpus = (50, 1)

            # gpu memory usage
            overall = 0
            overall_total = 0
            self.gpu_mem__node_used_total_index = []
            for n in sp_node:
                d = sp_node[n]
                gpus = list(d['gpu_total_memory'].keys())
                gpus.sort()
                for g in gpus:
                    used = d['gpu_used_memory'][g]
                    total = d['gpu_total_memory'][g]
                    overall += used
                    overall_total += total
                    self.gpu_mem__node_used_total_index.append((n, used, total, g))
            self.gpu_mem_total__used_alloc = (overall, overall_total)

        self.simple_output() if self.simple else self.enhanced_output()

    def __str__(self, compact=False):
        js_data = {'nodes': self.sp_node, 'total_time': self.diff, 'gpus': self.gpus}
        if compact:
            return json.dumps(js_data, separators=(',', ':'))
        else:
            return json.dumps(js_data, sort_keys=True, indent=4)

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
