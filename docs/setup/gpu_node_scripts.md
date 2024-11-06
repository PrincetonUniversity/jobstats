# GPU Job Statistics

GPU metrics (currently only NVIDIA) are collected by the <a href="https://github.com/plazonic/nvidia_gpu_prometheus_exporter" target="_blank">Jobstats GPU exporter</a> which was based on the exporter by Rohit Agarwal [[1]](https://github.com/mindprince/nvidia_gpu_prometheus_exporter). The main local changes were to add the handling of Multi-Instance GPUs (MIG) and two additional gauge metrics: `nvidia_gpu_jobId` and `nvidia_gpu_jobUid`. The table below lists all of the collected GPU fields. Note that the approach described here is not appropriate for clusters that allow for GPU sharing (e.g., sharding).

| Name | Description | Type |
| ---- | ----------- | ---- |
| `nvidia_gpu_duty_cycle` | GPU utilization | gauge |
| `nvidia_gpu_memory_total_bytes` | Total memory of the GPU device in bytes | gauge |
| `nvidia_gpu_memory_used_bytes`  | Memory used by the GPU device in bytes  | gauge |
| `nvidia_gpu_num_devices`        | Number of GPU devices gauge | gauge |
| `nvidia_gpu_power_usage_milliwatts` | Power usage of the GPU device in milliwatts | gauge |
| `nvidia_gpu_temperature_celsius`    | Temperature of the GPU device in Celsius | gauge |
| `nvidia_gpu_jobId` | JobId number of a job currently using this GPU as reported by Slurm | gauge |
| `nvidia_gpu_jobUid` | UID number of user running jobs on this GPU | gauge |


# GPU Job Ownership Helper

In order to correctly track which GPU is assigned to which `jobid`, we use Slurm prolog and epilog scripts to create files in `/run/gpustat`. These files are named either after GPU ordinal number (0, 1, ...) or, in the case of Multi-Instance GPUs (MIG), MIG-UUID. These files contain the space-separated `jobid` and `UID` number of the user, for example:

```
$ cat /run/gpustat/MIG-265a219d-a49f-578a-825d-222c72699c16
45916256 262563
```

These two scripts can be found in the `slurm` directory of the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/slurm" target="_blank">Jobstats GitHub repository</a>. For example, `slurm/epilog.d/gpustats_helper.sh` could be installed as `/etc/slurm/epilog.d/gpustats_helper.sh` and `slurm/prolog.d/gpustats_helper.sh` as `/etc/slurm/prolog.d/gpustats_helper.sh` with these `slurm.conf` statements:

```
Prolog=/etc/slurm/prolog.d/*.sh
Epilog=/etc/slurm/epilog.d/*.sh
```

For efficiency and simplicity, `JobId` and `jobUid` are collected from files in `/run/gpustat/0` (for GPU 0), `/run/gpustat/1` (for GPU 1), and so on. For example:

```
$ cat /run/gpustat/0
247609 223456
```

In the above, the first number is the `jobid` and the second is the `UID` number of the owning user. These are created with Slurm `prolog.d` and `epilog.d` scripts that can be found in the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/slurm" target="_blank">Jobstats GitHub repository</a>.
