# `reportseff`

The <a href="https://github.com/troycomi/reportseff" target="_blank">`reportseff`</a> utility wraps `sacct` to provide a cleaner user experience when interrogating Slurm job efficiency values for multiple jobs. In addition to multiple jobids, `reportseff` accepts Slurm output files as arguments and parses the jobid from the filename. Some `sacct` options are further wrapped or extended to simplify common operations. The output is a table with entries colored based on high/low utilization values. The columns and formatting of the table can be customized based on command line options.

A limit to the previous tools is that they provide information on a single job at a time in great detail. Another common use case is to summarize job efficiency for multiple jobs to gain a better idea of the overall utilization. Summarized reporting is especially useful with array jobs and workflow managers which interface with Slurm. In these cases, running `seff` or `jobstats` becomes burdensome.

## Usage

The `reportseff` tool accepts jobs as jobids, Slurm output files, and directories containing Slurm output files:

```
$ reportseff 123 124      # get information on jobs 123 and 124
$ reportseff {123..133}   # get information on jobs 123 to 133
$ reportseff jobname*     # check output files starting with jobname
$ reportseff slurm_out/   # look for output files in the slurm_out directory
```

The ability to link Slurm outputs with job status simplifies locating problematic jobs and cleaning up their outputs. The `reportseff` utility extends some of the `sacct` options. The start and end time can accept any format accepted by `sacct`, as well as a custom format, specified as a comma separated list of key/value pairs. For example:

```
$ reportseff --since now-27hours   # equivalent to
$ reportseff --since d=1,h=3       # 1 day, 3 hours
```

Filtering by job state is expanded with `reportseff` to specify states to exclude. This filtering combined with accepting output files helps in cleaning up failed output jobs:

```
$ reportseff --not-state CD     # not completed
             --since d=1 \      # today
             --format=jobid \   # just get file name
             my_failing_job* \  # only from these outputs
             | xargs grep "output:"
```

The last piece of the pipeline above find lines with the output directive to examine or delete. The format option can accept a comma-separated list of column names or additional columns can be appended to the default values. Appending prevents the need to add in the same, default columns on every invocation.

While the above features are available for any Slurm system, when Jobstats information is present in the `AdminComment`, the multi-node resource utilization is updated with the more accurate Jobstats values and GPU utilization is also provided. This additional information is controlled with the `--node` and `--node-and-gpu` options.

A sample workflow with `reportseff` is to run a series of jobs, each producing an output file. Run `reportseff` on the output directory to determine the utilization and state of each job. Jobs with low utilization or failure can be examined more closely by copy/pasting the Slurm output filename from the first column. Outputs from failed jobs can be cleaned automatically with a version of the command piping above. Combining with watch and aliases can create powerful monitoring for users:

```
# monitor the current directory every 5 minutes
$ watch -cn 300 reportseff --modified-sort

# monitor the user's efficiency every 10 minutes
$ watch -cn 600 reportseff --user $USER --modified-sort --format=+jobname
```

## Installation

The installation requirements for reportseff are Python 3.7+ and version 6.7+ of the Python `click` package which is used for creating colored text and command-line parsing. The Python code and instructions are available at <a href="https://github.com/troycomi/reportseff" target="_blank">https://github.com/troycomi/reportseff</a>.
