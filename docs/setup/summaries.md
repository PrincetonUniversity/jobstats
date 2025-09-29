# Generating Job Summaries

When all four exporters are used, the Prometheus database stores 17 metrics every N seconds for each job. It is recommended to retain this detailed data for several months or longer. This data can be visualized using the [Grafana dashboard](grafana.md). After some amount of time, it makes sense to purge the detailed data while keeping only a summary (i.e., CPU/GPU utilization and memory usage per node). The summary data can also be used in place of the detailed data when generating efficiency reports.

A summary of individual job statistics is generated at job completion and stored in the Slurm database (or [MariaDB](external-database.md)) in the `AdminComment` field. This is done by a `slurmctld` epilog script that runs at job completion. For example, in `slurm.conf`:


```
EpilogSlurmctld=/usr/local/sbin/slurmctldepilog.sh
```

The script is available in the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/slurm" target="_blank">Jobstats GitHub repository</a> and needs to be installed on the `slurmctld` server along with Jobstats. For storage efficiency and convenience, the JSON job summary data is gzipped and base64 encoded before being stored in the `AdminComment` field of the Slurm database (or [MariaDB](external-database.md)).

The impact on the database size due to this depends on job sizes. For an institution with 100,000 CPU-cores, for small jobs the `AdminComment` field tends to average under 50 characters per entry with a maximum under 1500 while for large jobs the maximum length is around 5000.

For processing old jobs where the `slurmctld` epilog script did not run or for jobs where it failed, there is a per cluster ingest Jobstats service. This is a Python-based script running on the `slurmdbd` host as a `systemd` timer and service, acting to query and modify the Slurm database directly. The script (`ingest_jobstats.py`) and `systemd` timer and service scripts are in the `slurm` directory of the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/slurm" target="_blank">Jobstats GitHub repository</a>.

Below is an example job summary for a GPU job:

```
$ jobstats 12345678 -j
{
    "gpus": 1,
    "nodes": {
        "della-k1g1": {
            "cpus": 12,
            "gpu_total_memory": {
                "1": 85899345920
            },
            "gpu_used_memory": {
                "1": 83314868224
            },
            "gpu_utilization": {
                "1": 98.6
            },
            "total_memory": 137438953472,
            "total_time": 57620.8,
            "used_memory": 84683702272
        }
    },
    "total_time": 50944
}
```


The following pipeline shows how the summary statistics are recovered from an `AdminComment` entry in the database:

```
$ sacct -j 823722 -n -o admincomment%250 | sed 's/JS1://' | tr -d ' ' | base64 -d | gzip -d | jq
{
  "nodes": {
    "della-l01g2": {
      "total_memory": 33554432000,
      "used_memory": 27482066944,
      "total_time": 8591.7,
      "cpus": 1,
      "gpu_total_memory": {
        "1": 10200547328
      },
      "gpu_used_memory": {
        "1": 124780544
      }
    }
  },
  "total_time": 432301,
  "gpus": 1
}
```

Only completed jobs have entries in the database.

## Using `pandas` to Analyze the Data

The Python code below can be used to work with the summary statistics in `AdminComment`:

```bash
$ wget https://raw.githubusercontent.com/PrincetonUniversity/job_defense_shield/refs/heads/main/src/job_defense_shield/efficiency.py
$ wget https://raw.githubusercontent.com/jdh4/saccta/refs/heads/main/gpu_usage.py
```

The script `gpu_usage.py` illustrates how to get the GPU utilization per job. The other functions in `efficiency.py` can be used to get the other metrics (e.g., `cpu_memory_usage`). See also the source code for [Job Defense Shield](https://github.com/PrincetonUniversity/job_defense_shield) where `efficiency.py` is used.
