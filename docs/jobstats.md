# Jobstats

Jobstats is a job monitoring platform composed of data exporters, Prometheus, Grafana and the Slurm database whereas `jobstats` is a command that operates on the Jobstats platform. If you are looking to setup the Jobstats platform then [see below](#jobstats-platform) and [this manuscript](https://tigress-web.princeton.edu/~jdh4/pearc23-97.pdf).

See our PEARC 2023 presentation: "Jobstats: A Slurm-Compatible Job Monitoring Platform for CPU and GPU Clusters" ([PDF](https://tigress-web.princeton.edu/~jdh4/jobstats_pearc_2023.pdf)). Here is our PEARC 2024 poster ([PDF](https://tigress-web.princeton.edu/~jdh4/jobstats_poster_PEARC2024_V2.pdf)).

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

For completed jobs, the data is taken from a call to sacct with several fields including AdminComment. For running jobs, the Prometheus database must be queried.

Importantly, the `jobstats` command is also used to replace `smail`, which is the Slurm executable used for sending email reports that are based on `seff`. This means that users receive emails that are the exact output of `jobstats` including the notes.

### Installation

The installation requirements for `jobstats` are Python 3.6+, [Requests 2.20+](https://pypi.org/project/requests/) and (optionally) [blessed 1.17+](https://pypi.org/project/blessed/) which can be used for coloring and styling text.

The necessary software can be installed as follows:

```bash
$ conda create --name js-env python=3.7 requests blessed -c conda-forge
```

After setting up the Jobstats platform (see below), to start using the `jobstats` command on your system, run these commands:

```bash
$ git clone https://github.com/PrincetonUniversity/jobstats.git
$ cd jobstats
# use a text editor to create config.py (see the example configuration file below)
$ chmod u+x jobstats
$ ./jobstats 1234567
```

### Configuration File

Use `config.py` as the starting point for your configuration file.

# Jobstats Platform









### JSON Output

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

# Users of the Jobstats Platform

- Brown University
- Free University of Berlin
- Princeton Computer Science
- Princeton Research Computing
- Yale University
- and more
