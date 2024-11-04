# Grafana

Follow the directions at [grafana.com](https://grafana.com/).

Grafana dashboard json that uses all of the exporters is included in the grafana subdirectory. It expects one parameter, jobid. As it may not be easy to find the time range we also use an ondemand job stats helper that generates the correct time range given a jobid, documented in the next section.

The following image illustrates what the dashboard looks like in use:

<center><img src="https://tigress-web.princeton.edu/~jdh4/jobstats_grafana.png"></center>

Eleven of the seventeen metrics abovearenode-level. This means that if multiple jobs are running on the node then it will not be possible to disentangle thedata.Tousethesemetricstotroubleshoot jobs, the job should allocate the entire node. The complete Grafana interface for the Jobstats platform is composed of plots of the time history of the seventeen quantities above. An example of the Grafana dashboard and the needed code are available in the Jobstats GitHub repository [17]. This graphical interface is used for detailed investigations such as troubleshooting failed jobs, identifying jobs with CPU memory leaks, intermittent GPUusage, load imbalance, and for understanding the anomalous behavior of system hardware. While the Grafana interface is an essential component of the Jobstats platform, for quick inspections of job behavior, the jobstats command is used. This tool and four others are discussed in Section 3.

The four exporters lead to a wealth of data in the Prometheus database. To visualize this data, the Grafana visualization toolkit [24] is used. The following job-level metrics are available in both Grafana and the jobstats command:

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

Eleven of the seventeen metrics above are node-level. This means that if multiple jobs are running on the node then it will not be possible to disentangle the data. To use the metrics to troubleshoot jobs, the job should allocate the entire node.

The complete Grafana interface for the Jobstats platform is composed of plots of the time history of the seventeen quantities above. An example of the Grafana dashboard and the needed code are available in the Jobstats GitHub repository [17]. This graphical interface is used for detailed investigations such as troubleshooting failed jobs, identifying jobs with CPU memory leaks, intermittent GPUusage, load imbalance, and for understanding the anomalous behavior of system hardware.

While the Grafana interface is an essential component of the Jobstats platform, for quick inspections of job behavior, the jobstats command is used. This tool and four others are discussed in Section 3.
