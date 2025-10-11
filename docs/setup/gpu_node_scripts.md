# GPU Job Statistics

GPU metrics (currently only NVIDIA) are collected by the <a href="https://github.com/plazonic/nvidia_gpu_prometheus_exporter" target="_blank">Jobstats GPU exporter</a> which was based on the exporter by Rohit Agarwal [[1]](https://github.com/mindprince/nvidia_gpu_prometheus_exporter). The main local changes were to add the handling of Multi-Instance GPUs (MIG) and two additional gauge metrics: `nvidia_gpu_jobId` and `nvidia_gpu_jobUid`. The table below lists all of the collected GPU fields.

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

!!! note

    Note that the approach described here is not appropriate for clusters that allow for GPU sharing (e.g., sharding).


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

For efficiency and simplicity, `JobId` and `jobUid` are collected from files in either '/run/gpustat/UUID-OF-THE-GPU` (e.g. `/run/gpustat/GPU-03aa20a1-2e97-d125-629d-fd4e5734553f`) or `/run/gpustat/0` (for GPU 0), `/run/gpustat/1` (for GPU 1), and so on. For example:

```
$ cat /run/gpustat/0
247609 223456
```

In the above, the first number is the `jobid` and the second is the `UID` number of the owning user. These are created with Slurm `prolog.d` and `epilog.d` scripts that can be found in the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/slurm" target="_blank">Jobstats GitHub repository</a>.

# GPU Ownership Caveats

Depending on your slurm gres configuration you may need to change either prolog/epilog scripts or gres.conf in order to match correctly GPUs to jobs running on them. The problem is in the difference between GPU ordinal number and its minor number. Slurm's gres.conf can make CUDA_VISIBLE_DEVICES in prolog/epilog scripts be the (recommended) ordinal number, the minor number or even something entirely different.

The ordinal number corresponds to the order of how GPUs are displayed in the nvidia-smi output where they are sorted by their PCI/BUS-id number (lowest one is #0, and so on). This is also the number you have to use in CUDA_VISIBLE_DEVICES or as a parameter to `nvidia-smi -i` option.

A GPU minor number corresponds to its `/dev/nvidiaX` number. One way to see GPU minor numbers would be to run the following:

```
# grep 'Device Minor' /proc/driver/nvidia/gpus/*/information
/proc/driver/nvidia/gpus/0000:07:00.0/information:Device Minor: 	 2
/proc/driver/nvidia/gpus/0000:0b:00.0/information:Device Minor: 	 3
/proc/driver/nvidia/gpus/0000:48:00.0/information:Device Minor: 	 0
/proc/driver/nvidia/gpus/0000:4c:00.0/information:Device Minor: 	 1
/proc/driver/nvidia/gpus/0000:88:00.0/information:Device Minor: 	 6
/proc/driver/nvidia/gpus/0000:8b:00.0/information:Device Minor: 	 7
/proc/driver/nvidia/gpus/0000:c8:00.0/information:Device Minor: 	 4
/proc/driver/nvidia/gpus/0000:cb:00.0/information:Device Minor: 	 5
```

The above is the output from a GPU node where ordinal number does not match its GPU minor number and where GPU#0 is `/dev/nvidia2` and *not* `/dev/nvidia0`.

How can this cause a problem and incorrect stats? Let's assume a job that requests a single GPU and slurm allocates it the GPU#0, on a node where ordinal!=minor, as illustrated above.

If you configured your GPU nodes with gres.conf that contains `AutoDetect=nvml` slurm will, through its use of nvidia libraries, give you the GPU with PCI-ID `0000:07:00.0` with ordinal number 0 and `/dev/nvidia2` device. In `/etc/slurm/prolog/epilog` scripts `CUDA_VISIBLE_DEVICES` is set to 0 and `nvidia-smi -i 0` will fetch the correct UUID and therefore properly set the `/run/gpustat/0` and `/run/gpustat/GPU-UUID` files. User's job will be given access (via devices cgroup) to the `/dev/nvidia2` - so everything matches and therefore status will match the actual utilization.

On the other hand, when gres.conf is configured as follows:

```
Name=gpu Type=a100 Count=8 File=/dev/nvidia[0-7]
```

slurm will assume that GPU#0 is `/dev/nvidia0` (GPU#1 is `/dev/nvidia1`, ...).  In `/etc/slurm/prolog/epilog` scripts slurm will still set `CUDA_VISIBLE_DEVICES` to 0 but now as far as `nvidia-smi -i 0` that's actually the GPU with `/dev/nvidia2` which will not match what the user will be given access to in the job (`/dev/nvidia0`). Hence the incorrect data collection.

One obvious fix would be to stick with `AutoDetect=nvml`. Another would be to not attempt to use UUID's for data collection, that is to remove

```
  if [ "${i:0:3}" != "MIG" ]; then
    UUID="`/usr/bin/nvidia-smi --query-gpu=uuid --format=noheader,csv -i $i`"
    echo $SLURM_JOB_ID $SLURM_JOB_UID > "$DEST/$UUID"
  fi
```

which will make it rely only on the numbers in `CUDA_VISIBLE_DEVICES`. Note that this relies on using a recent version of our `nvidia_gpu_exporter` that defaults to using minor numbers in `/run/gpustats`.

You could also set gres.conf by hand correctly:

```
Name=gpu Type=a100 Count=8 File=/dev/nvidia2,/dev/nvidia3,/dev/nvidia0,/dev/nvidia1,/dev/nvidia6,/dev/nvidia7,/dev/nvidia4,/dev/nvidia5
```

Finally, assuming `File=/dev/nvidia[0-7]` config (so use of minor numbers) you can figure out the ordinal number in the script, e.g.:

```
#!/bin/bash
DEST=/run/gpustat
[ -e $DEST ] || mkdir -m 755 $DEST
for i in ${GPU_DEVICE_ORDINAL//,/ } ${CUDA_VISIBLE_DEVICES//,/ }; do
  if [ "${i:0:3}" != "MIG" ]; then
    PCI_ID=`egrep "Device Minor:[[:space:]]+${i}$" /proc/driver/nvidia/gpus/*/information|cut -d/ -f6`
    UUID=`/usr/bin/nvidia-smi --query-gpu=uuid --format=noheader,csv -i $PCI_ID`
    INDEX=`/usr/bin/nvidia-smi --query-gpu=index --format=noheader,csv -i $PCI_ID`
    echo $SLURM_JOB_ID $SLURM_JOB_UID > "$DEST/$INDEX"
    echo $SLURM_JOB_ID $SLURM_JOB_UID > "$DEST/$UUID"
  else
  echo $SLURM_JOB_ID $SLURM_JOB_UID > $DEST/$i
  fi
done
exit 0
```
