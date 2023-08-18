Jobstats is a job monitoring platform composed of data exporters, Prometheus, Grafana and the Slurm database whereas `jobstats` is a command that operates on the Jobstats platform. If you are looking to setup the Jobstats platform then [see below](#jobstats-platform) and [this manuscript](https://tigress-web.princeton.edu/~jdh4/pearc23-97.pdf).

See our PEARC 2023 presentation: "Jobstats: A Slurm-Compatible Job Monitoring Platform for CPU and GPU Clusters" ([PDF](https://tigress-web.princeton.edu/~jdh4/jobstats_pearc_2023.pdf)).

# jobstats

The `jobstats` command provides users with a Slurm job efficiency report for a given jobid:

```
$ jobstats 39798795

================================================================================
                              Slurm Job Statistics
================================================================================
         Job ID: 39798795
  NetID/Account: aturing/math
       Job Name: sys_logic_ordinals
          State: COMPLETED
          Nodes: 2
      CPU Cores: 48
     CPU Memory: 256GB (5.3GB per CPU-core)
           GPUs: 4
  QOS/Partition: della-gpu/gpu
        Cluster: della
     Start Time: Fri Mar 4, 2022 at 1:56 AM
       Run Time: 18:41:56
     Time Limit: 4-00:00:00

                              Overall Utilization
================================================================================
  CPU utilization  [|||||                                          10%]
  CPU memory usage [|||                                             6%]
  GPU utilization  [||||||||||||||||||||||||||||||||||             68%]
  GPU memory usage [|||||||||||||||||||||||||||||||||              66%]

                              Detailed Utilization
================================================================================
  CPU utilization per node (CPU time used/run time)
      della-i14g2: 1-21:41:20/18-16:46:24 (efficiency=10.2%)
      della-i14g3: 1-18:48:55/18-16:46:24 (efficiency=9.5%)
  Total used/runtime: 3-16:30:16/37-09:32:48, efficiency=9.9%

  CPU memory usage per node - used/allocated
      della-i14g2: 7.9GB/128.0GB (335.5MB/5.3GB per core of 24)
      della-i14g3: 7.8GB/128.0GB (334.6MB/5.3GB per core of 24)
  Total used/allocated: 15.7GB/256.0GB (335.1MB/5.3GB per core of 48)

  GPU utilization per node
      della-i14g2 (GPU 0): 65.7%
      della-i14g2 (GPU 1): 64.5%
      della-i14g3 (GPU 0): 72.9%
      della-i14g3 (GPU 1): 67.5%

  GPU memory usage per node - maximum used/total
      della-i14g2 (GPU 0): 26.5GB/40.0GB (66.2%)
      della-i14g2 (GPU 1): 26.5GB/40.0GB (66.2%)
      della-i14g3 (GPU 0): 26.5GB/40.0GB (66.2%)
      della-i14g3 (GPU 1): 26.5GB/40.0GB (66.2%)

                                     Notes
================================================================================
  * This job only used 6% of the 256GB of total allocated CPU memory. For
    future jobs, please allocate less memory by using a Slurm directive such
    as --mem-per-cpu=1G or --mem=10G. This will reduce your queue times and
    make the resources available to other users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/memory

  * This job only needed 19% of the requested time which was 4-00:00:00. For
    future jobs, please request less time by modifying the --time Slurm
    directive. This will lower your queue times and allow the Slurm job
    scheduler to work more effectively for all users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/slurm

  * For additional job metrics including metrics plotted against time:
    https://mydella.princeton.edu/pun/sys/jobstats  (VPN required off-campus)
```

One can also output the raw JSON:

```
$ jobstats -j 39798795 | jq
{
  "gpus": 4,
  "nodes": {
    "della-i14g2": {
      "cpus": 24,
      "gpu_total_memory": {
        "0": 42949672960,
        "1": 42949672960
      },
      "gpu_used_memory": {
        "0": 28453568512,
        "1": 28453568512
      },
      "gpu_utilization": {
        "0": 65.7,
        "1": 64.5
      },
      "total_memory": 137438953472,
      "total_time": 164480.1,
      "used_memory": 8444272640
    },
    "della-i14g3": {
      "cpus": 24,
      "gpu_total_memory": {
        "0": 42949672960,
        "1": 42949672960
      },
      "gpu_used_memory": {
        "0": 28453634048,
        "1": 28453634048
      },
      "gpu_utilization": {
        "0": 72.9,
        "1": 67.5
      },
      "total_memory": 137438953472,
      "total_time": 154135.9,
      "used_memory": 8419606528
    }
  },
  "total_time": 67316
}
```

For completed jobs, the data is taken from a call to sacct with several fields including AdminComment. For running jobs, the Prometheus database must be queried.

Importantly, the `jobstats` command is also used to replace `smail`, which is the Slurm executable used for sending email reports that are based on `seff`. This means that users receive emails that are the exact output of `jobstats` including the notes.

### Installation

The installation requirements for `jobstats` are Python 3.6+ and version 1.17+ of the Python `blessed` package which is used for coloring and styling text.

# Jobstats Platform

Below is an outline of the steps that need to be taken to setup the Jobstats platform for a Slurm cluster:

- Switch to cgroup based job accounting from Linux process accounting 
- Setup the exporters: cgroup, node, GPU (on the nodes) and, optionally, GPFS (centrally)
- Setup the prolog.d and epilog.d scripts on the GPU nodes
- Setup the Prometheus server and configure it to scrape data from the compute nodes and all configured exporters
- Setup the slurmctldepilog.sh script for long-term job summary retention
- Lastly, configure Grafana and Open OnDemand

### Exporters

We use these four exporters:
- node exporter: https://github.com/prometheus/node_exporter
- cgroup exporter: https://github.com/plazonic/cgroup_exporter
- nvidia gpu exporter: https://github.com/plazonic/nvidia_gpu_prometheus_exporter
- gpfs exporter: https://github.com/plazonic/gpfs-exporter

### Basic Prometheus Configuration
What follows is an example of production configuration used for the Tiger cluster that has both regular and GPU nodes.
```
---
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: master
- job_name: Tiger Nodes
  scrape_interval: 30s
  scrape_timeout: 30s
  file_sd_configs:
  - files:
    - "/etc/prometheus/local_files_sd_config.d/tigernodes.json"
  metric_relabel_configs:
  - source_labels:
    - __name__
    regex: "^go_.*"
    action: drop
- job_name: TigerGPU Nodes
  scrape_interval: 30s
  scrape_timeout: 30s
  file_sd_configs:
  - files:
    - "/etc/prometheus/local_files_sd_config.d/tigergpus.json"
  metric_relabel_configs:
  - source_labels:
    - __name__
    regex: "^go_.*"
    action: drop
```
tigernode.json looks like:
```
 [
   {
     "labels": {
       "cluster": "tiger"
     },
     "targets": [
       "tiger-h19c1n10:9100",
       "tiger-h19c1n10:9306",
       ...
     ]
   }
 ]
```
where both node_exporter (port 9100) and cgroup_exporter (port 9306) are listed, for all of tiger's nodes. tigergpus.json looks very similar except that it collects data from nvidia_gpu_prometheus_exporter on port 9445.

Note the additional label cluster.

### GPU Job Ownership Helper
In order to correctly track which GPU is assigned to which jobid we use slurm prolog and epilog scripts to create files in ```/run/gpustat``` directory named either after GPU ordinal number (0, 1, ..) or, in the case of MIG cards, MIG-UUID. These files contain space separated jobid and uid number of the user. E.g.
```
# cat /run/gpustat/MIG-265a219d-a49f-578a-825d-222c72699c16
45916256 262563
```
These two scripts can be found in the slurm directory. For example, slurm/epilog.d/gpustats_helper.sh could be installed as /etc/slurm/epilog.d/gpustats_helper.sh and slurm/prolog.d/gpustats_helper.sh as /etc/slurm/prolog.d/gpustats_helper.sh with these slurm.conf config statements:
```
 Prolog=/etc/slurm/prolog.d/*.sh
 Epilog=/etc/slurm/epilog.d/*.sh
```

### Grafana

Grafana dashboard json that uses all of the exporters is included in the grafana subdirectory. It expects one parameter, jobid. As it may not be easy to find the time range we also use an ondemand job stats helper that generates the correct time range given a jobid, documented in the next section.

The following image illustrates what the dashboard looks like in use:

<center><img src="https://tigress-web.princeton.edu/~jdh4/jobstats_grafana.png"></center>

### Open OnDemand JobStats Helper

ood-jobstats-helper subdirectory contains an Open OnDemand app that, given a job id, uses sacct to generate a full Grafana URL with job's jobid, start and end times.

### Generating Job Summaries

Job summaries, as described above, are generated and stored in the Slurm database at the end of each job by using slurmctld epilog script, e.g.:

```
EpilogSlurmctld=/usr/local/sbin/slurmctldepilog.sh
```

The script can be found in the slurm subdirectory, named "slurmctldepilog.sh".

For processing old jobs where slurmctld epilog script did not run or for jobs where it failed there is a per cluster ingest jobstats service. This is a python based script running on the slurmdbd host, as a systemd timer and service, querying and modifying slurm database directly. The script (ingest_jobstats.py) and systemd timer and service scripts are in the slurm directory. 

We made heavy use of this script to generate job summaries for older jobs but with the current version of the Epilog script it should not be needed anymore.

### Job email script
We use slurm/jobstats_mail.sh as the slurm's Mail program. E.g. from slurm.conf:
```
MailProg=/usr/local/bin/jobstats_mail.sh
````
This will include jobstats information for jobs that have requested email notifications on completion.

### Notes

The `jobstats` command analyzes each job and produces custom notes at the bottom of the output. Below are several examples:

```
  * This job ran on the mig partition where each job is limited to 1 MIG
    GPU, 1 CPU-core, 10 GB of GPU memory and 32 GB of CPU memory. A MIG GPU
    is about 1/7th as powerful as an A100 GPU. Please continue using the mig
    partition when possible. For more info:
      https://researchcomputing.princeton.edu/systems/della#gpus

  * This job completed while only needing 19% of the requested time which
    was 2-00:00:00. For future jobs, please decrease the value of the --time
    Slurm directive. This will lower your queue times and allow the Slurm
    job scheduler to work more effectively for all users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/slurm

  * This job did not use the GPU. Please resolve this before running
    additional jobs. Wasting resources prevents other users from getting
    their work done and it causes your subsequent jobs to have a lower
    priority. Is the code GPU-enabled? Please consult the documentation for
    the code. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing

  * This job only used 15% of the 100GB of total allocated CPU memory.
    Please consider allocating less memory by using the Slurm directive
    --mem-per-cpu=3G or --mem=18G. This will reduce your queue times and
    make the resources available to other users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/memory

  * This job ran on a large-memory (datascience) node but it only used 117
    GB of CPU memory. The large-memory nodes should only be used for jobs
    that require more than 190 GB. Please allocate less memory by using the
    Slurm directive --mem-per-cpu=9G or --mem=150G. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/memory

  * The CPU utilization of this job (24%) is approximately equal to 1
    divided by the number of allocated CPU-cores (1/4=25%). This suggests
    that you may be running a code that can only use 1 CPU-core. If this is
    true then allocating more than 1 CPU-core is wasteful. Please consult
    the documentation for the software to see if it is parallelized. For
    more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/parallel-code

  * This job did not use the CPU. This suggests that something went wrong at
    the very beginning of the job. Check your Slurm script for errors and
    look for useful information in the file slurm-46987157.out if it exists.

  * The Tiger cluster is intended for jobs that require multiple nodes. This
    job ran in the serial partition where jobs are assigned the lowest
    priority. On Tiger, a job will run in the serial partition if it only
    requires 1 node. Consider carrying out this work elsewhere.

  * For additional job metrics including metrics plotted against time:
      https://mystellar.princeton.edu/pun/sys/jobstats  (VPN required off-campus)

  * For additional job metrics including metrics plotted against time:
      https://stats.rc.princeton.edu  (VPN required off-campus)
```

# Tools of the Jobstats Platform

In addition to `jobstats`, the following software tools build on the Jobstats platform:

- [gpudash](https://github.com/PrincetonUniversity/gpudash) - A command for generating a text-based GPU utilization dashboard   
- [job defense shield](https://github.com/PrincetonUniversity/job_defense_shield) - A tool for sending automated email alerts to users  
- [reportseff](https://github.com/troycomi/reportseff) - A command for displaying Slurm efficiency reports for several jobs at once
- [utilization reports](https://github.com/PrincetonUniversity/monthly_sponsor_reports) - A tool for sending detailed usage reports to users by email
