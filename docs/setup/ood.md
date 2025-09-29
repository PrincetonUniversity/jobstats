# Open OnDemand Jobstats Helper

See the `ood-jobstats-helper` directory in the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/ood-jobstats-helper" target="_blank">Jobstats GitHub repository</a>. This directory contains an Open OnDemand app that, given a `jobid`, uses `sacct` to generate a full Grafana URL with the `jobid`, start time and end time.

As of July 2025, the Open OnDemand helper app supports noninteractive redirect to the Grafana dashboard for a given `jobid`. This makes it possible to add notes such as the following to the `jobstats` output:

```
* See the URL below for various job metrics plotted as a function of time:
    https://mydella.princeton.edu/pun/sys/jobstats/39798795
```

When a browser is pointed at the URL above, the Grafana webpage for the job (containing the 17 metrics versus time) is displayed.
