# Node Statistics

The Prometheus <a href="https://github.com/prometheus/node_exporter" target="_blank">`node_exporter`</a> should be setup to run on every compute node. This allows the Jobstats platform to obtain basic node metrics such as total memory available, memory usage, CPU frequencies, NFS statistics, Infiniband statistics and many other potentially useful quantities. Spectrum Scale/GPFS statistics are collected with a <a href="https://github.com/plazonic/gpfs-exporter" target="_blank">custom Python-based exporter</a>.

Proceed to the next section on [Job Summaries](summaries.md).
