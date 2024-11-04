# Setup Overview

Below is an outline of the steps that need to be taken to setup the Jobstats platform for a Slurm cluster:

1. Switch to cgroup-based job accounting from Linux process accounting 
2. Setup the exporters: cgroup, node, GPU (on the nodes) and, optionally, GPFS (centrally)
3. Setup the `prolog.d` and `epilog.d` scripts on the GPU nodes
4. Setup the Prometheus server and configure it to scrape the data from the compute nodes
5. Setup the `slurmctldepilog.sh` script for long-term job summary retention
6. Lastly, configure the Grafana interface and Open OnDemand

A single standard server has proven to be sufficient for a data center with 100,000 CPU-cores and 1000 GPUs.
