# Jobstats setup

Below is an outline of the steps that need to be taken to setup the Jobstats platform for a Slurm cluster:

- Switch to cgroup based job accounting from Linux process accounting 
- Setup the exporters: cgroup, node, GPU (on the nodes) and, optionally, GPFS (centrally)
- Setup the prolog.d and epilog.d scripts on the GPU nodes
- Setup the Prometheus server and configure it to scrape data from the compute nodes and all configured exporters
- Setup the slurmctldepilog.sh script for long-term job summary retention
- Lastly, configure Grafana and Open OnDemand

## Exporters

These exporters are used:

- node exporter: https://github.com/prometheus/node_exporter
- cgroup exporter: https://github.com/plazonic/cgroup_exporter
- nvidia gpu exporter: https://github.com/plazonic/nvidia_gpu_prometheus_exporter
- gpfs exporter: https://github.com/plazonic/gpfs-exporter

## Basic Prometheus Configuration
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

## GPU Job Ownership Helper

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

## Grafana

Grafana dashboard json that uses all of the exporters is included in the grafana subdirectory. It expects one parameter, jobid. As it may not be easy to find the time range we also use an ondemand job stats helper that generates the correct time range given a jobid, documented in the next section.

The following image illustrates what the dashboard looks like in use:

<center><img src="https://tigress-web.princeton.edu/~jdh4/jobstats_grafana.png"></center>

## Open OnDemand JobStats Helper

ood-jobstats-helper subdirectory contains an Open OnDemand app that, given a job id, uses sacct to generate a full Grafana URL with job's jobid, start and end times.

## Generating Job Summaries

Job summaries, as described above, are generated and stored in the Slurm database at the end of each job by using slurmctld epilog script, e.g.:

```
EpilogSlurmctld=/usr/local/sbin/slurmctldepilog.sh
```

The script can be found in the slurm subdirectory, named "slurmctldepilog.sh".

For processing old jobs where slurmctld epilog script did not run or for jobs where it failed there is a per cluster ingest jobstats service. This is a python based script running on the slurmdbd host, as a systemd timer and service, querying and modifying slurm database directly. The script (ingest_jobstats.py) and systemd timer and service scripts are in the slurm directory. 

We made heavy use of this script to generate job summaries for older jobs but with the current version of the Epilog script it should not be needed anymore.

## Job email script
We use slurm/jobstats_mail.sh as the slurm's Mail program. E.g. from slurm.conf:
```
MailProg=/usr/local/bin/jobstats_mail.sh
````
This will include jobstats information for jobs that have requested email notifications on completion.
