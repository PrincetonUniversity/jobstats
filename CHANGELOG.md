# Changelog

This document lists important changes, in particular ones that might require system intervention, like Prometheus exporter or `jobstats` updates.

## [1.1.0] - October 5, 2026

### September 2, 2026 - Detailed GPU Metrics
Jobstats can be configured to collect [detailed GPU metrics](https://princetonuniversity.github.io/jobstats/setup/detailed_gpu_metrics/) using NVML. This applies to NVIDIA Hopper GPUs and later (e.g., H100, H200, B100, B200, B300, R100). Use version 0.2.3+ of the [NVIDIA GPU exporter](https://github.com/plazonic/nvidia_gpu_prometheus_exporter). 

### June 11, 2026 - Memory used/shmem change
GPU jobs will frequently use shared memory as does tmpfs use `/dev/shm` and this has not been properly accounted for in Jobstats. Version 0.3.2 of [cgroup_exporter](https://github.com/plazonic/cgroup_exporter) now adds the `shmem` metric in cgroupv2. If Jobstats finds this metric it will add it to the total memory usage of the job. To use this, upgrade both the cgroup_exporter and Jobstats.

### June 4, 2026 - SLUID Slurm 26.05 change
As of Slurm 26.05 when Slurm creates cgroupv2 directories it will now by default use the `SLUID` of the job instead of the previous `job_<JOBID>`.

There are two ways to fix this. The easiest and best one is to configure Slurm to continue using `jobid` by setting `CgroupJobIdPaths=yes`. There is no downside to this choice. This option was added in 26.05.2 and 26.11.

Alternatively, you can also update to at least v0.3.1 of [cgroup_exporter](https://github.com/plazonic/cgroup_exporter) and to a current version of `jobstats`. The new version of `cgroup_exporter` will detect `SLUID` and use it for the `jobid` label. Jobstats will now query for `jobid` and `SLUID` when fetching stats from Prometheus.

### May 27, 2026 - Nvidia gpu exporter jobid change
The [NVIDIA GPU exporter](https://github.com/plazonic/nvidia_gpu_prometheus_exporter) has since September 2025 started adding `jobid` labels to all of the collected job metrics. We have now added support for using these labels for job matching, instead of using `nvidia_gpu_jobId` metric. For any larger or longer jobs this makes GPU Prometheus queries considerably faster.

If you haven't been running a recent version of `nvidia_gpu_prometheus_exporter` then please consider upgrading (especially because it also collects GPM metrics on newer GPUs) and then turn on new processing by setting `GPU_EXPORTER_JOBID = True` in `config.py`.

## [1.0.0] - October 26, 2025

First release of the software.
