# Jobstats and jobstats

Jobstats is a job monitoring platform composed of data exporters, Prometheus, Grafana and the Slurm database whereas `jobstats` is a command that operates on the Jobstats platform. If you are looking to setup the Jobstats platform then [see below](#jobstats-platform).




## jobstats

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
  * This job requested 5.3 GB of memory per CPU-core. Given that the overall
    CPU memory usage was only 6%, please consider reducing your CPU memory
    allocation for future jobs. This will reduce your queue times and make the
    resources available for other users. For more info:
    https://researchcomputing.princeton.edu/support/knowledge-base/memory

  * The time efficiency of this job is 19%. The time efficiency is the run time
    divided by the time limit. For future jobs please consider decreasing the
    value of the --time directive to increase the time efficiency. This will
    lower your queue time and allow the Slurm job scheduler to work more
    effectively for all users. For more info:
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

## Jobstats Platform

### Exporters

There are four exporters.

### Grafana

Visualization

### Generating Job Summaries

Job summaries, as described above, are generated and stored in the Slurm database at the end of each job by using slurmctld epilog script, e.g.:

```
EpilogSlurmctld=/usr/local/sbin/slurmctldepilog
```

Below is the script:

```
#!/bin/bash
# it looks like that this is sometimes too fast, wait a tiny bit to let slurmdbd get the data it needs
sleep 5s
if [ "x$SLURM_ARRAY_JOB_ID" = "x$SLURM_JOB_ID" ]; then
        INTERNAL_JOBID=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}
else
        INTERNAL_JOBID=$SLURM_JOB_ID
fi
logger SlurmctldEpilog[$INTERNAL_JOBID]: Begin processing
STATS="`jobstats -f -b $SLURM_JOB_ID`"
ERR=$?
if [ $ERR = 0 ]; then
        if None|H4s) ; then
                logger "SlurmctldEpilog[$INTERNAL_JOBID]: Success with output $STATS"
                OUT="`sacctmgr -i update job where jobid=$INTERNAL_JOBID set AdminComment=JS1:$STATS 2>&1`"
                if [ $? != 0 ]; then
                        logger "SlurmctldEpilog[$INTERNAL_JOBID]: Errored out when storing AdminComment with $OUT"
                fi
        else
                logger "SlurmctldEpilog[$INTERNAL_JOBID]: Apparent success but invalid output $STATS"
        fi
else
        logger "SlurmctldEpilog[$INTERNAL_JOBID]: Failed to process with error $ERR and output $STATS"
fi
logger SlurmctldEpilog[$INTERNAL_JOBID]: End processing
exit 0
```

Note the special treatment of array jobs where array job id is equal to the job id - this is because setting AdminComment for such jobs would overwrite AdminComments for all of array jobs with that array job id. Therefore those jobs have to be referred to with `${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}` rather than `$SLURM_JOB_ID`.

For processing old jobs where slurmctld epilog script did not run or for jobs where it failed for some reason we have a per cluster ingest jobstats service. This is running on the slurmdbd host, as a systemd timer and service. E.g. for della cluster:

```
$ cat /etc/systemd/system/ingest_jobstats-della.timer
[Unit]
Description=Timer for jobstats data ingest into cluster della database tables
Requires=ingest_jobstats-della.service

[Timer]
Unit=ingest_jobstats-della.service
#OnCalendar=*:0/4
OnBootSec=10min
OnUnitActiveSec=4min

[Install]
WantedBy=timers.target
```

and the service:

```
$ cat /etc/systemd/system/ingest_jobstats-della.timer
[Unit]
Description=Timer for jobstats data ingest into cluster della database tables
Requires=ingest_jobstats-della.service

[Timer]
Unit=ingest_jobstats-della.service
#OnCalendar=*:0/4
OnBootSec=10min
OnUnitActiveSec=4min

[Install]
WantedBy=timers.target
[root@db ~]# cat /etc/systemd/system/ingest_jobstats-della.service 
[Unit]
Description=Ingest jobstats data into cluster della database tables
Wants=ingest_jobstats-della.timer

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/ingest_jobstats -c della -n 1000

[Install]
WantedBy=multi-user.target
```

The **FIXME--ingest_jobstats** is a python script that queries and modifies the slurm database directly. Hopefully slurm will add a way to securely modify all array jobs and at that point this ingest method should not be needed.

### OnDemand Helper Script

### Other






