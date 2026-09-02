# Detailed GPU Metrics

Jobstats provides the following detailed GPU metrics:

```
                     SM | OCC |  TC | INT | FP16 Max | FP32 Avg | FP64 Max | PCIe Recv | PCIe Sent | NVLink Recv | NVLink Sent | Power | Temp
                    ----+-----+-----+-----+----------+----------+----------+-----------+-----------+-------------+-------------+-------+-----
della-k1g2 (GPU 4)  40% | 10% | 15% |  6% |     0.9% |     0.0% |     0.0% |    71MB/s |    12MB/s |      25GB/s |      25GB/s | 346 W | 46°C
della-k1g2 (GPU 5)  30% | 10% | 15% |  6% |     0.9% |     0.0% |     0.0% |    68MB/s |    12MB/s |      25GB/s |      25GB/s | 337 W | 43°C
della-k1g2 (GPU 6)  40% | 10% | 15% |  6% |     0.9% |     0.0% |     0.0% |    69MB/s |    12MB/s |      25GB/s |      25GB/s | 351 W | 46°C
della-k1g2 (GPU 7)  30% | 10% | 15% |  6% |     0.9% |     0.0% |     0.0% |    69MB/s |    12MB/s |      25GB/s |      25GB/s | 355 W | 45°C
```

At Princeton Research Computing, these GPU metrics are measured every 30 seconds. Below is the definition of each:

- `SM` is streaming multiprocessor (SM) utilization. The quantity measures the average activity of the streaming multiprocessors (SMs) on your GPU or the percentage of all available SMs that are currently active. An SM is considered active if it has at least one warp (a bundle of 32 threads) assigned to it. This metric is the ratio of cycles where SMs had active warps compared to the total possible cycles, averaged across all SMs on the chip. For reference, an NVIDIA H100 SXM GPU has 132 SMs. This quantity varies from 0 to 100%. SM utilization is less than or equal to GPU utilization.
- `OCC` is occupancy which measures the time-averaged ratio of active threads (or warps) currently running on a processing core to the maximum possible number that can fit on that core at one time, averaged over all cores. It compares how many parallel execution units (called warps or wavefronts) are active on a streaming multiprocessor against the absolute limit of the hardware. This quantity varies from 0 to 100%.

    An occupancy of 100% does not always mean best performance. If a task has enough active threads to hide memory delays, pushing occupancy higher can crowd hardware resources and hurt overall speed. Occupancy is typically less than both GPU utilization and SM utilization.
- `TC` is Tensor Core utilization which is the time-averaged percentage of time that the specialized AI hardware Tensor Cores were actively working during a specific measurement interval. It tracks activity across all supported precision types (e.g., FP16, BF16, INT8, or TF32). For reference, an NVIDIA H100 SXM GPU has 528 Tensor Cores. This quantity varies from 0 to 100%. Deep learning codes like PyTorch will automatically use the Tensor Cores when possible.
- `FP16 Max` is the maximum value of the measurements of the percentage of time that the half-precision (FP16) arithmetic pipes/cores of the GPU were active over the lifetime of the job. This quantity varies from 0 to 100%. Note that FP16 operations performed on the Tensor Cores are not included by this metric.
- `FP32 Avg` is the time average of the measurements of the percentage of time that the single-precision (FP32) arithmetic pipes/cores were active. This quantity varies from 0 to 100%.
- `FP64 Max` is the maximum value of the measurements of the percentage of time that the double-precision (FP64) arithmetic pipes/cores were active. This quantity varies from 0 to 100%.
- `INT` is the time average of the measurements of the percentage of time that the integer (INT) arithmetic pipes/cores were active. This quantity varies from 0 to 100%.
- `PCIe Recv` is the rate of data being transmitted to the GPU from the host (CPU/system memory) over the PCIe bus. PCIe (Peripheral Component Interconnect Express) is the high-speed communication bus that connects the GPU to the CPU and the rest of the computer. In a deep learning training workload, batches of data are almost continuously sent from the CPU to the GPU. The maximum value for this metric is typically tens of gigabytes per second.
- `PCIe Sent` is the rate of data being transmitted from the GPU to the host (CPU/system memory) over the PCIe bus. In simpler terms, it measures how fast the GPU is "sending" data back to the rest of the computer.
- `NVLink Sent` is the averge value of the measurements of the aggregate rate at which a GPU sends data over its NVLink connections during the brief measurement interval. NVLink is a high-speed GPU-to-GPU interconnect that enables fast data transfers. For example, during multi-GPU AI training, GPUs frequently exchange gradients or other tensors. If that communication goes over NVLink rather than PCIe, a significant performance gain can be achieved. If you have access to a multi-GPU node, run the command `nvidia-smi topo -m` to see the NVLink topology and interconnect map. Not all GPU systems provide NVLink. Single-GPU jobs will not use NVLink.
- `NVLink Recv` is the averge value of the measurements of the aggregate rate at which the GPU receives data over all of its NVLink connections during the brief measurement interval.
- `Power` is the time-averaged GPU power usage in units of Watts.
- `Temp` is the time-averaged temperature in units of Celsius.
- `GPU utilization` is the percentage of time that a GPU kernel is running on the GPU. This quantity is independent of the number of threads being used. It varies between 0 to 100%. The instantaneous value of this metric can be obtained by running the `nvidia-smi` command.

## Configuration for System Administrators

Jobstats can be configured to collect detailed GPU metrics using either NVML or DCGM. This applies to NVIDIA Hopper GPUs and later (e.g., H100, H200, B100, B200, B300, R100). It is recommended to use the NVML exporter since it is lightweight and it does not conflict with profilers such as NVIDIA Nsight.

In `config.py`, set the exporter:

```python
GPU_METRICS_EXPORTER = "NVML"  # choices are "None", "NVML" or "DCGM"
```

For `"NVML"` use version 0.2.3+ of the [Jobstats (NVIDIA) Prometheus exporter](https://github.com/plazonic/nvidia_gpu_prometheus_exporter/).

Each GPU metric is specified as a Python dictionary in the configuration file:

```python
GPU_METRICS = {}
GPU_METRICS["TC"] = {"metric": "tensor_cores",
                     "operation": "avg_over_time",
                     "show_overall": True,
                     "show_per_gpu": True,
                     "write_to_db": False,
                     "long_name": "Tensor Core utilization"}
```

The choices for "metric" are:

- `"duty_cycle"`
- `"sm"`
- `"occupancy"`
- `"fp16"`
- `"fp32"`
- `"fp64"`
- `"integer"`
- `"tensor_cores"`
- `"memory_used_bytes"`
- `"power_usage_milliwatts"`
- `"temperature_celsius"`
- `"pcie_rx_per_sec"`
- `"pcie_tx_per_sec"`
- `"nvlink_total_rx_per_sec"`
- `"nvlink_total_tx_per_sec"`

The choices for "operation" are:
 
- `"min_over_time"`
- `"avg_over_time"`
- `"max_over_time"`
- `"stddev_over_time"`

Each site can construct a custom set of metrics by selecting different `"metric"` and `"operation"`. See `config.py` in the Jobstats GitHub repository for examples.

To see the overall utilization of a metric choose `"show_overall": True`. This will produced a text-based meter in the output.
Using `"write_to_db": True` will cause the metric to be stored the `AdminComment` field at job completion in either the Slurm database or an external MySQL/MariaDB database if configured. The metric will then be available when the `jobstats` command is run.

## Metrics

### GPU Utilization

The percentage of time that a GPU kernel is running on the GPU. This quantity is independent of the number of threads being used.

This quantity varies from 0 to 100%.

Most users are familar with this metric from the `nvidia-smi` command.

The example below returns the maximum GPU utilization:

```python
GPU_METRICS["GPU Util (max)"] = {"metric": "duty_cycle",
                                 "operation": "max_over_time",
                                 "show_overall": True,
                                 "show_per_gpu": True,
                                 "write_to_db": False}
```

### Streaming Multiprocessor Utilization

Measures the average activity of the Streaming Multiprocessors (SMs) on your GPU or the percentage of all available SMs that are currently active. An SM is considered active if it has at least one warp (a bundle of 32 threads) assigned to it. This metric is the ratio of cycles where SMs had active warps compared to the total possible cycles, averaged across all SMs on the chip.

SM utilization is less than or equal GPU utilization.

Below is a sample configuration entry:

```python
GPU_METRICS["SM"] = {"metric": "sm_util_percent",
                     "operation": "avg_over_time",
                     "show_overall": True,
                     "show_per_gpu": True,
                     "write_to_db": False,
                     "long_name": "Streaming Multiprocessor (SM) utilization"}
```


### Occupancy

GPU occupancy measures the ratio of active threads or warps currently running on a processing core to the maximum possible number that can fit on that core at one time. It compares how many parallel execution units (called warps or wavefronts) are active on a streaming multiprocessor against the absolute limit of the hardware.

An occupancy of 100% does not always mean best performance. If a task has enough active threads to hide memory delays, pushing occupancy higher can crowd hardware resources and hurt overall speed.

Occupancy utilization tends to fall below both GPU utilization and SM utilization.

Below is a sample configuration entry:

```python
GPU_METRICS["OCC"] = {"metric": "sm_occupancy_percent",
                      "operation": "avg_over_time",
                      "show_overall": True,
                      "show_per_gpu": True,
                      "write_to_db": False,
                      "long_name": "Occupancy"}
```

### Power

The power per GPU is available.

```python
GPU_METRICS["Power (mW)"] = {"metric": "power_usage_milliwatts",
                             "operation": "avg_over_time",
                             "show_overall": False,
                             "show_per_gpu": True,
                             "write_to_db": False,
                             "long_name": "Power Usage"}
```

### Temperature

The temperature per GPU in units of Celsius is available.

```python
GPU_METRICS["Temp. (C)"] = {"metric": "temperature_celsius",
                            "operation": "avg_over_time",
                            "show_overall": False,
                            "show_per_gpu": True,
                            "write_to_db": False,
                            "long_name": "Temperature"}
```

### Tensor Core Utilization

Percentage of the time that the specialized AI hardware Tensor Cores were actively working during a specific measurement interval. It tracks activity across all supported precision types (e.g., FP16, BF16, INT8, or TF32).

This quantity varies from 0 to 100%.

```python
GPU_METRICS["TC"] = {"metric": "any_tensor_util_percent",
                     "operation": "avg_over_time",
                     "show_overall": True,
                     "show_per_gpu": True,
                     "write_to_db": False,
                     "long_name": "Tensor Core (TC) utilization"}
```

### FP16/FP32/FP64 Utilization

Percentage of time the GPU's half-precision (FP16) arithmetic pipes/cores were active over a sample period.

These three quantities each vary from 0 to 100%.

Consider looking at FP64 with `max_over_time` on a cluster for AI research to find codes that are using double precision.


### Integer Utilization

Percentage of time the integer arithmetic pipes/cores were active over a sample period.

This quantity varies from 0 to 100%.


### GPU to CPU Data Transfer Rate

The metric `nvidia_gpu_pcie_tx_per_sec` represents the rate of data being transmitted from the GPU to the host (CPU/system memory) over the PCIe bus. In simpler terms, it measures how fast the GPU is "sending" data back to the rest of the computer.


### Data Transfer Rate to the GPU

The metric `nvidia_gpu_pcie_rx_per_sec` represents the rate of data being transmitted to the GPU over the PCIe bus.

The metric `nvidia_gpu_pcie_rx_per_sec` represents the rate of data being received by the GPU over the PCIe (Peripheral Component Interconnect Express) bus. In the context of GPU monitoring, this metric tracks the throughput of "Host-to-Device" (H2D) communication—essentially how fast data is moving from your CPU/System RAM into the GPU’s memory.

### NVLink Data Rate (Received)

The metric `nvidia_gpu_nvlink_total_rx_per_sec` represents the total rate of data being received by a specific GPU across all its active NVLink connections, measured in bytes per second. This is a critical performance counter used in high-performance computing (HPC) and deep learning environments to monitor how efficiently GPUs are communicating with one another. If this number is pinned at the maximum theoretical bandwidth of your hardware, your workload is "communication-bound." It helps ensure that your software (like NCCL for PyTorch or TensorFlow) is actually using NVLink rather than falling back to the much slower PCIe bus. A sudden drop in this value during a heavy workload could indicate a hardware failure or a "degraded" link where one or more NVLink lanes have shut down.

### NVLink Data Rate (Transmitted)

Sames as above but data transmitted from the GPU.

## Comparison Between NVML and DCGM

The table below illustrates the differences in the metrics between NVML and DCGM:

| NVML field | DCGM metric | Equivalent? | Notes |
|---|---|---|---|
| `nvidia_gpu_sm_occupancy_percent` | `DCGM_FI_PROF_SM_OCCUPANCY` | **Exact** | Percentage of theoretical maximum resident warps. |
| `nvidia_gpu_sm_util_percent` | `DCGM_FI_PROF_SM_ACTIVE` | **Very close / exact concept** | Percentage of cycles in which an SM has ≥1 warp assigned. |
| `nvidia_gpu_fp16_util_percent` | `DCGM_FI_PROF_PIPE_FP16_ACTIVE` | **Exact** | FP16 pipe activity; **does not include HMMA tensor operations**. |
| `nvidia_gpu_fp32_util_percent` | `DCGM_FI_PROF_PIPE_FP32_ACTIVE` | **Exact** | FP32 pipe activity. |
| `nvidia_gpu_fp64_util_percent` | `DCGM_FI_PROF_PIPE_FP64_ACTIVE` | **Exact** | FP64 pipe activity. |
| `nvidia_gpu_integer_util` | `DCGM_FI_PROF_PIPE_INT_ACTIVE` | **Exact** | Integer pipe activity. |
| `nvidia_gpu_duty_cycle` | `DCGM_FI_DEV_GPU_UTIL` | **Approximate** | General GPU utilization; probably the closest DCGM equivalent. |
| `nvidia_gpu_memory_used_bytes` | `DCGM_FI_DEV_FB_USED` | **Exact concept** | DCGM reports MiB rather than bytes; multiply by `1024²`. |
| `nvidia_gpu_memory_total_bytes` | `DCGM_FI_DEV_FB_TOTAL` | **Exact concept** | If available in your DCGM version; otherwise derive from used + free. |
| `nvidia_gpu_any_tensor_util_percent` | `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | **Exact** | Activity of tensor pipelines. |
| `nvidia_gpu_pcie_rx_per_sec` | `DCGM_FI_PROF_PCIE_RX_BYTES` | **Exact concept** | Bytes received over PCIe; depending on exporter, this may already be a rate. |
| `nvidia_gpu_pcie_tx_per_sec` | `DCGM_FI_PROF_PCIE_TX_BYTES` | **Exact concept** | Bytes transmitted over PCIe. |
| `nvidia_gpu_nvlink_total_rx_per_sec` | `DCGM_FI_PROF_NVLINK_RX_BYTES` | **Exact concept** | NVLink RX traffic; aggregate across links if necessary. |
| `nvidia_gpu_nvlink_total_tx_per_sec` | `DCGM_FI_PROF_NVLINK_TX_BYTES` | **Exact concept** | NVLink TX traffic; aggregate across links if necessary. |

## Custom Job Notes

The overall utilization value of metrics that are a percentage (e.g., "FP16") with `"show_overall: True"` can be referenced in the notes with:

```
self.gm_overall["<SHORT-NAME>-util"]
```

Below are two example notes for a GPU cluster intended for AI research:

```python
condition = '(self.js.cluster == "della") and ("pli" in self.js.partition) and (self.gm_overall["TC-util"] == 0) and self.js.is_retained()'
note = ("The Tensor Core utilization of the job was 0%. Usually AI codes use the Tensor Cores. Should your code be using them?")
style = "normal"
NOTES.append((condition, note, style))
```

```python
condition = '(self.js.cluster == "della") and ("pli" in self.js.partition) and (self.gm_overall["FP64 (max)-util"] > 0) and self.js.is_retained()'
note = ("The FP64 utilization of the job was {self.gm_overall[\'FP64 (max)-util\']}%. Usually AI codes do not use 64-bit arithmetic.")
style = "normal"
NOTES.append((condition, note, style))
```
