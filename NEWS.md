This document lists important changes, in particular ones that might require system intervention, like Prometheus exporter or jobstats updates.

### June 4, 2026 - SLUID Slurm 26.05 change
As of Slurm 26.05 when slurm creates cgroupv2 directories it will now use job's SLUID instead of the previous job\_JOBID. For cpu and memory statistics to continue being tracked correctly make sure to update to at least v0.3.1 of [cgroup_exporter](https://github.com/plazonic/cgroup_exporter) and to a current version of jobstats. The new version of cgroup\_exporter will detect SLUID and use it for the jobid label. Jobstats will now query for jobid and SLUID when fetching stats from Prometheus.

### May 27, 2026 - Nvidia gpu exporter jobid change
The [nvidia gpu exporter](https://github.com/plazonic/nvidia_gpu_prometheus_exporter) has since September 2025 started adding jobid labels to all of the collected job metrics. We have now added support for using these labels for job matching, instead of using `nvidia_gpu_jobId` metric. For any larger/longer this makes GPU Prometheus queries considerably faster.

If you haven't been running newer version of nvidia\_gpu\_prometheus\_exporter please consider upgrading (especially because it also collects GPM metrics on newer GPUs) and then turn on new processing by setting `GPU_EXPORTER_JOBID = True` in `config.py`.
