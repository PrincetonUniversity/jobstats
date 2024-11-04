# Generating Job Summaries

Job summaries, as described previously, are generated and stored in the Slurm database at the end of each job by using a `slurmctld epilog` script. For example, in `slurm.conf`:

```
EpilogSlurmctld=/usr/local/sbin/slurmctldepilog.sh
```

The script is available in the [Jobstats GitHub repository](https://github.com/PrincetonUniversity/jobstats/tree/main/slurm). For storage efficiency and convenience, the JSON job summary data is gzipped and base64 encoded before being stored in the `AdminComment` field of the Slurm database. The impact on the database size due to this depends on job sizes. On our clusters, for small jobs the `AdminComment` field tends to average under 50 characters per entry with a maximum under 1500 while for large jobs the maximum length is around 5000.

For processing old jobs where `slurmctld` epilog script did not run or for jobs where it failed there is a per cluster ingest jobstats service. This is a Python based script running on the `slurmdbd` host, as a `systemd` timer and service, querying and modifying Slurm database directly. The script (`ingest_jobstats.py`) and `systemd` timer and service scripts are in the Slurm directory.
