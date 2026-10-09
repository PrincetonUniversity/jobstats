# Detailed GPU Metrics

Jobstats provides detailed GPU metrics such as those below:

```
                     SM | OCC |  TC | INT | FP16 Max | FP32 Avg | FP64 Max | DRAM BW | Power | Temp
                    ----+-----+-----+-----+----------+----------+----------+---------+-------+-----
della-k1g2 (GPU 4)  40% | 10% | 15% |  6% |     0.9% |    20.0% |     0.0% |     30% | 346 W | 46°C
della-k1g2 (GPU 5)  30% | 10% | 15% |  6% |     0.9% |    22.1% |     0.0% |     25% | 337 W | 43°C
della-k1g2 (GPU 6)  40% | 10% | 15% |  6% |     0.9% |    20.0% |     0.0% |     30% | 351 W | 46°C
della-k1g2 (GPU 7)  30% | 10% | 15% |  6% |     0.9% |    22.0% |     0.0% |     25% | 355 W | 45°C

                    PCIe Recv | PCIe Sent | NVLink Recv | NVLink Sent
                    ----------+-----------+-------------+------------
della-k1g2 (GPU 4)    71 MB/s |   12 MB/s |     25 GB/s |     25 GB/s
della-k1g2 (GPU 5)    68 MB/s |   12 MB/s |     25 GB/s |     25 GB/s
della-k1g2 (GPU 6)    69 MB/s |   12 MB/s |     25 GB/s |     25 GB/s
della-k1g2 (GPU 7)    69 MB/s |   12 MB/s |     25 GB/s |     25 GB/s
```

These GPU metrics are measured every tens of seconds or every few minutes depending on the configuration at your institution. Different institutions record different metrics. These measurements are only available on the Hopper GPU architecture (e.g., H100) and newer.

Below are the definitions of the metrics shown above:

- `SM` is streaming multiprocessor (SM) utilization. The quantity measures the average activity of the streaming multiprocessors (SMs) on your GPU or the percentage of all available SMs that are currently active. An SM is considered active if it has at least one warp (a bundle of 32 threads) assigned to it. This metric is the ratio of cycles where SMs had active warps compared to the total possible cycles, averaged across all SMs on the chip. For reference, an NVIDIA H100 SXM GPU has 132 SMs. This quantity varies from 0 to 100%. SM utilization is less than or equal to GPU utilization.
- `OCC` is occupancy which measures the time-averaged ratio of active threads (or warps) currently running on a processing core to the maximum possible number that can fit on that core at one time, averaged over all cores. It compares how many parallel execution units (called warps or wavefronts) are active on a streaming multiprocessor against the absolute limit of the hardware. This quantity varies from 0 to 100%. An occupancy of 100% does not always mean best performance. If a task has enough active threads to hide memory delays, pushing occupancy higher can crowd hardware resources and hurt overall speed. Occupancy is typically less than both GPU utilization and SM utilization.
- `TC` is Tensor Core utilization which is the time-averaged percentage of time that the specialized AI hardware Tensor Cores were actively working during a specific measurement interval. It tracks activity across all supported precision types (e.g., FP16, BF16, INT8, or TF32). For reference, an NVIDIA H100 SXM GPU has 528 Tensor Cores. This quantity varies from 0 to 100%. Deep learning codes like PyTorch will automatically use the Tensor Cores when possible.
- `INT` is the time average of the measurements of the percentage of time that the integer (INT) arithmetic pipes/cores were active. This quantity varies from 0 to 100%.
- `FP16 Max` is the maximum value of the measurements of the percentage of time that the half-precision (FP16) arithmetic pipes/cores of the GPU were active over the lifetime of the job. This quantity varies from 0 to 100%. Note that FP16 operations performed on the Tensor Cores are not included by this metric.
- `FP32 Avg` is the time average of the measurements of the percentage of time that the single-precision (FP32) arithmetic pipes/cores were active. This quantity varies from 0 to 100%.
- `FP64 Max` is the maximum value of the measurements of the percentage of time that the double-precision (FP64) arithmetic pipes/cores were active. This quantity varies from 0 to 100%.
- `DRAM BW` is the percentage of the GPU's theoretical maximum DRAM memory bandwidth that is being used. This relates to data movement between the GPU memory and the GPU streaming multiprocessors  where the numerical operations are carried out. For reference, an NVIDIA H100 SXM GPU has a theoretical maximum DRAM memory bandwidth of 3.35 TB/s. This quantity varies from 0 to 100%. High SM utilization with low DRAM BW utilization suggests compute-heavy work, while low/moderate SM utilization with high DRAM BW utilization is a strong indication of a memory-bandwidth-bound application.
- `Power` is the time-averaged GPU power usage in units of Watts.
- `Temp` is the time-averaged temperature in units of Celsius.
- `PCIe Recv` is the rate of data being transmitted to the GPU from the host (CPU/system memory) over the PCIe bus. PCIe (Peripheral Component Interconnect Express) is the high-speed communication bus that connects the GPU to the CPU and the rest of the computer. In a deep learning training workload, batches of data are almost continuously sent from the CPU to the GPU. The maximum value for this metric is typically tens of gigabytes per second.
- `PCIe Sent` is the rate of data being transmitted from the GPU to the host (CPU/system memory) over the PCIe bus. In simpler terms, it measures how fast the GPU is "sending" data back to the rest of the computer.
- `NVLink Sent` is the averge value of the measurements of the aggregate rate at which a GPU sends data over its NVLink connections during the brief measurement interval. NVLink is a high-speed GPU-to-GPU interconnect that enables fast data transfers. For example, during multi-GPU AI training, GPUs frequently exchange gradients or other tensors. If that communication goes over NVLink rather than PCIe, a significant performance gain can be achieved. If you have access to a multi-GPU node, run the command `nvidia-smi topo -m` to see the NVLink topology and interconnect map. Not all GPU systems provide NVLink. Single-GPU jobs will not use NVLink.
- `NVLink Recv` is the averge value of the measurements of the aggregate rate at which the GPU receives data over all of its NVLink connections during the brief measurement interval.
- `GPU utilization` is the percentage of time that a GPU kernel is running on the GPU. This quantity is independent of the number of threads being used. It varies between 0 to 100%. The instantaneous value of this metric can be obtained by running the `nvidia-smi` command.

## Configuration for System Administrators

Jobstats can be configured to collect detailed GPU metrics using NVML. This applies to NVIDIA Hopper GPUs and later (e.g., H100, H200, B100, B200, B300, R100). It may be possible to also support DCGM with contributions from the community. However, it is recommended to use the NVML exporter over DCGM since it is lightweight and it does not conflict with profilers such as NVIDIA Nsight.

In `config.py`, set the exporter:

```python
GPU_METRICS_EXPORTER = "NVML"  # choices are "None" or "NVML" (or "DCGM")
```

For `"NVML"` use version 0.2.3+ of the [Jobstats (NVIDIA) Prometheus exporter](https://github.com/plazonic/nvidia_gpu_prometheus_exporter/). Note that the "DCGM" choice is not fully supported. Sites are encouraged to use "NVML". Contributions are welcome for the DCGM approach (please open a GitHub issue to discuss this).

Set the URL to the documentation for the detailed GPU metrics:

```python
GPU_METRICS_DOCS_URL = "https://princetonuniversity.github.io/jobstats/setup/detailed_gpu_metrics"
```

If you do not want to display a URL then use `GPU_METRICS_DOCS_URL = ""`.

Each GPU metric is specified as a Python dictionary in the configuration file, for example:

```python
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
- `"dram_bw_util_percent"`
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

Each site can construct a custom set of metrics. See `config.py` in the Jobstats GitHub repository for examples.

To see the overall utilization of a metric choose `"show_overall": True`. This will produced a text-based meter in the output. This should only be done for quantities that are reported as a percentage.

Using `"write_to_db": True` will cause the metric to be stored in the `AdminComment` field at job completion in either the Slurm database or an [external MySQL/MariaDB database](external-database.md). The metric will then be available when the `jobstats` command is run. Using `show_per_gpu: True` will show the metric value for each GPU in the "Detailed Utilization" section of the output. Lastly, `"long_name"` will be used in the "Detailed Utilization" section if the concise table format is not used.

One or more tables will be used to display the data if there are four detailed metrics or more. Otherwise, the data will be displayed as lines of text. Metrics with a name containing "PCIe" or "NVLink" will be displayed in a separate table.

## Example Metrics

Below is a simple example entry for `config.py` with three metrics:

```python
################################################################################
##                 D E T A I L E D    G P U    M E T R I C S                  ##
################################################################################
GPU_METRICS_EXPORTER = "NVML"
GPU_METRICS_DOCS_URL = "https://princetonuniversity.github.io/jobstats/setup/detailed_gpu_metrics/"
GPU_METRICS = {}
GPU_METRICS["SM"] = {"metric": "sm_util_percent",
                     "operation": "avg_over_time",
                     "show_overall": True,
                     "show_per_gpu": True,
                     "write_to_db": True,
                     "long_name": "Streaming Multiprocessor (SM) utilization"}
GPU_METRICS["DRAM BW"] = {"metric": "dram_bw_util_percent",
                          "operation": "avg_over_time",
                          "show_overall": True,
                          "show_per_gpu": True,
                          "write_to_db": True,
                          "long_name": "DRAM Bandwidth utilization"}
GPU_METRICS["Power"] = {"metric": "power_usage_milliwatts",
                        "operation": "avg_over_time",
                        "show_overall": False,
                        "show_per_gpu": True,
                        "write_to_db": True,
                        "long_name": "Power Usage"}
```

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

Below is an example note for a GPU cluster intended for AI research:

```python
condition = '(self.js.cluster == "della") and ("pli" in self.js.partition) and (self.gm_overall["TC-util"] == 0) and self.js.is_retained()'
note = ("The Tensor Core utilization of the job was 0%. Usually AI codes use the Tensor Cores. Should your code be using them?")
style = "normal"
NOTES.append((condition, note, style))
```
