# CPU Job Statistics

Slurm has to be configured to track job accounting data via the cgroup plug-in. This requires the following line in `slurm.conf`:

```
JobAcctGatherType=jobacct_gather/cgroup
```

The above is in addition to the other usual cgroup-related plug-ins/settings:

```
ProctrackType=proctrack/cgroup
TaskPlugin=affinity,cgroup
```

Slurm will then create two top-level cgroup directories for each job, one for CPU utilization and one for CPU memory. Within each directory there will be subdirectories: `step_extern`, `step_batch`, `step_0`, `step_1`, and so on. Within these directories one finds `task_0`, `task_1`, and so on. These cgroups are scraped by a <a href="https://github.com/plazonic/cgroup_exporter" target="_blank">cgroup exporter</a>. The table below lists all of the collected fields:

| Name | Description | Type |
| ---- | ----------- | ---- |
| `cgroup_cpu_system_seconds` | Cumulative CPU system seconds for jobid | gauge |
| `cgroup_cpu_total_seconds`  | Cumulative CPU total seconds for jobid | gauge |
| `cgroup_cpu_user_seconds`   | Cumulative CPU user seconds for jobid | gauge |
| `cgroup_cpus` | Number of CPUs in the jobid | gauge |
| `cgroup_memory_cache_bytes` | Memory cache used in bytes | gauge |
| `cgroup_memory_fail_count` | Memory fail count | gauge |
| `cgroup_memory_rss_bytes`  | Memory RSS used in bytes | gauge |
| `cgroup_memory_total_bytes` | Memory total given to jobid in bytes | gauge |
| `cgroup_memory_used_bytes`  | Memory used in bytes | gauge |
| `cgroup_memsw_fail_count`   | Swap fail count | gauge |
| `cgroup_memsw_total_bytes`  | Swap total given to jobid in bytes | gauge |
| `cgroup_memsw_used_bytes`   | Swap used in bytes | gauge |
| `cgroup_uid`                | UID number of user running this job | gauge |

The cgroup exporter used here is based on the exporter by Trey Dock [[1]](https://github.com/treydock/cgroup_exporter) with additional parsing of the `jobid`, `steps`, `tasks` and `UID` number. This produces an output that resembles (e.g., for system seconds):

```
cgroup_cpu_system_seconds{jobid="247463", step="batch", task="0"}
160.92
```

Note that the UID of the owning user is stored as a gauge in `cgroup_uid`:

```
cgroup_uid{jobid="247463"}
334987
```

This is because accounting is job-oriented and having a UID of the user as a label would needlessly increase the cardinality of the data in Prometheus. All other fields are alike with `jobid`, `step` and `task` labels.

The totals for a job have an empty `step` and `task`, for example:

```
cgroup_cpu_user_seconds{jobid="247463", step="", task=""}
202435.71
```

This is due to the organization of the cgroup hierarchy. Consider the directory:

```
/sys/fs/cgroup/cpu,cpuacct/slurm/uid_334987
```

Within this directory, one finds the following subdirectories:

```
job_247463/cpuacct.usage_user
job_247463/step_extern/cpuacct.usage_user
job_247463/step_extern/task_0/cpuacct.usage_user
```

This is the data most often retrieved and parsed for overall job efficiency which is why by default the `cgroup_exporter` does not parse `step` or `task` data. To collect all of it, add the `--collect.fullslurm option`. We run the `cgroup_exporter` with these options:

```
/usr/sbin/cgroup_exporter --config.paths /slurm --collect.fullslurm
```

The `--config.paths /slurm` has to match the path used by Slurm under the top cgroup directory. This is usually a path that is something like `/sys/fs/cgroup/memory/slurm`.
