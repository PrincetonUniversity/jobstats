# GPU Job Statistics

GPU metrics (currently only NVIDIA) are collected by our exporter [19] which was based on Ref. [1]. The main local changes were to add the handling of Multi-Instance GPUs (MIG) and two additional gauge metrics: `nvidia_gpu_jobId` and `nvidia_gpu_jobUid`. Table 2 lists all of the collected GPU fields. Note that the approach described here is not appropriate for clusters that allow for GPU sharing (e.g., sharding). In Section 3, we demonstrate how the GPU metrics stored in the Prometheus database can be queried by tools that generate dashboards and utilization reports.

| Name | Description | Type |
| ---- | ----------- | ---- |
| nvidia_gpu_duty_cycle | GPU utilization | gauge |
| nvidia_gpu_memory_total_bytes | Total memory of the GPU device in bytes | gauge |
| nvidia_gpu_memory_used_bytes  | Memory used by the GPU device in bytes  | gauge |
| nvidia_gpu_num_devices        | Number of GPU devices gauge | gauge |
| nvidia_gpu_power_usage_milliwatts | Power usage of the GPU device in milliwatts | gauge |
| nvidia_gpu_temperature_celsius    | Temperature of the GPU device in Celsius | gauge |
| nvidia_gpu_jobId | JobId number of a job currently using this GPU as reported by Slurm | gauge |
| nvidia_gpu_jobUid | UID number of user running jobs on this GPU | gauge |

# GPU Job Ownership Helper

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

For efficiency and simplicity, JobId and jobUid are collected from files in /run/gpustat/0 (for GPU 0), /run/gpustat/1 (for GPU 1), and so on. For example:

```
$ cat /run/gpustat/0 247609 223456
```

In the above, the first number is the jobid and the second is the UID number for that job’s owning user. These are created with Slurm prolog.d and epilog.d scripts that can be found in the Jobstats GitHub repository [20].
