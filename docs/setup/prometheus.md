# Prometheus

Prometheus is a monitoring system and time series database. For setup, follow the directions at [prometheus.io](https://prometheus.io/). The Prometheus exporters required for the Jobstats platform were discussed in the previous sections.

## Basic Prometheus Configuration

Below is an example of the production configuration for the Tiger cluster that has both CPU and GPU nodes:

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

The `tigernode.json` file looks like:

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

Both `node_exporter` (port 9100) and `cgroup_exporter` (port 9306) are listed for all of the nodes in `tigernode.json`. The file `tigergpus.json` looks very similar except that it collects data from `nvidia_gpu_prometheus_exporter` on port 9445. Note the additional `cluster` label.
