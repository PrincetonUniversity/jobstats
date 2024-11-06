# Grafana

The four exporters lead to a wealth of data in the Prometheus database. To visualize this data, the Grafana visualization toolkit is used. To setup Grafana follow the directions at <a href="https://grafana.com" target="_blank">grafana.com</a>.

Grafana dashboard JSON file that uses all of the exporters is included in the `grafana` subdirectory in the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/grafana" target="_blank">Jobstats GitHub repository</a>. It expects one parameter, `jobid`. As it may not be easy to find the time range of the job, we also use an OnDemand helper that generates the correct time range given a `jobid` (see the [next section](ood.md)).

The following job-level metrics are available in both Grafana and the `jobstats` command:

- CPU Utilization
- CPU Memory Utilization
- GPU Utilization 
- GPU Memory Utilization 

The following additional job-level metrics are exposed only in Grafana:

- GPU Power Usage
- GPU Temperature 

Finally, the following additional node-level metrics are exposed only in Grafana:

- CPU Percentage Utilization
- Total Memory Utilization
- Mean Frequency Over All CPUs
- NFS Statistics
- Local Disc R/W
- GPFS Bandwidth Statistics
- Local Disc IOPS
- GPFS Operations per Second Statistics 
- Infiniband Throughput
- Infiniband Packet Rate
- Infiniband Errors

Eleven of the seventeen metrics above are node-level. This means that if multiple jobs are running on the node then it will not be possible to disentangle the data.To use these metrics to troubleshoot jobs, the job should allocate the entire node. The complete Grafana interface for the Jobstats platform is composed of plots of the time history of the seventeen quantities above. This graphical interface is used for detailed investigations such as troubleshooting failed jobs, identifying jobs with CPU memory leaks, intermittent GPU usage, load imbalance, and for understanding the anomalous behavior of system hardware.

The following image illustrates what the dashboard looks like in use:

<center><img src="https://tigress-web.princeton.edu/~jdh4/grafana_dashboard_single.jpg"></center>
