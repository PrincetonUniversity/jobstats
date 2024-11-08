# The `jobstats` command

The last step in setting up the Jobstats platform is installing the `jobstats` command. This command generates the job efficiency report. For completed jobs, the data is available in the Slurm database. For actively running jobs, the Prometheus database must be queried to obtain the data needed to generate the report.

## Installation

The installation requirements for `jobstats` are Python 3.6+, [Requests 2.20+](https://pypi.org/project/requests/) and (optionally) [blessed 1.17+](https://pypi.org/project/blessed/) which can be used for coloring and styling text.

The necessary software can be installed as follows:

=== "Ubuntu"

    ```
    $ apt-get install python3-requests python3-blessed
    ```

=== "conda"

    ```bash
    $ conda create --name js-env python=3.7 requests blessed -c conda-forge
    ```

=== "pip"

    ```bash
    $ python3 -m venv .venv
    $ source .venv/bin/activate
    (.venv) $ pip3 install requests blessed
    ``` 

The four files needed to run the `jobstats` command are available in the <a href="https://github.com/PrincetonUniversity/jobstats" target="_blank">Jobstats GitHub repository</a>:

```
$ ls -l /usr/local/bin
config.py
jobstats
jobstats.py
output_formatters.py
```

Remember to change the permissions to make `jobstats` executable. An overview of the command can be seen by looking at the help menu:

```
$ jobstats --help
```

The command takes the `jobid` as the only required argument:

```
$ jobstats 12345678
```


## Configuration File

The `jobstats` command requires a `config.py` configuration file. Use `config.py` in the [Jobstats GitHub repository](https://github.com/PrincetonUniversity/jobstats) as the starting point for your configuration.

The first entry in `config.py` is for the Prometheus server:

```python
# prometheus server address and port
PROM_SERVER = "http://vigilant2:8480"
```

The number of seconds between measurements by the exporters on the compute nodes:

```
# number of seconds between measurements
SAMPLING_PERIOD = 30
```

The value above should match that in the Prometheus configuration, i.e., `scrape_interval: 30s`.

One can use the Python `blessed` package to produce bold and colorized text. This
helps to draw attention to specific lines of the report. This part
of the configuration sets the various thresholds:

```
# threshold values for red versus black notes
GPU_UTIL_RED   = 15  # percentage
GPU_UTIL_BLACK = 25  # percentage
CPU_UTIL_RED   = 65  # percentage
CPU_UTIL_BLACK = 80  # percentage
TIME_EFFICIENCY_RED   = 40  # percentage
TIME_EFFICIENCY_BLACK = 70  # percentage
```

For instance, if the overal GPU utilization is less than 15% then it will be displayed in bold red text. Search
the conditions in the example notes in `config.py` to see how the other values are used.

The following threshold can be used to trigger notes about excessive CPU memory usage:

```
MIN_MEMORY_USAGE = 70  # percentage
```

Notes can be suppressed if the run time of the job is less than the following threshold:

```
MIN_RUNTIME_SECONDS = 10 * SAMPLING_PERIOD  # seconds
```

Use `CLUSTER_TRANS` to convert informal cluster names to the name that is used in the Slurm database.
For instance, if the `tiger` cluster is replaced by the `tiger2` cluster then use:

```
CLUSTER_TRANS = {"tiger":"tiger2"}
CLUSTER_TRANS_INV = dict(zip(CLUSTER_TRANS.values(), CLUSTER_TRANS.keys()))
```

This will allow users to specify `tiger` as the cluster while internally the value `tiger2` is used
when querying the Slurm database.

One can trim long job names:

```
# maximum number of characters to display in jobname
MAX_JOBNAME_LEN = 64
```

Notes concerning excessive CPU memory allocations may require the values of the default memory per CPU-core:

```
# default CPU memory per core in bytes for each cluster
# if unsure then use memory per node divided by cores per node
DEFAULT_MEM_PER_CORE = {"adroit":3_355_443_200,
                        "della":4_194_304_000,
                        "stellar":7_864_320_000,
                        "tiger":4_294_967_296,
                        "traverse":7_812_500_000}
```

In Python, one can specify a large number like 1 billion as `1_000_000_000`.

Similarly, the number of CPU-cores per node for each cluster is required for certain notes to be triggered:

```
# number of CPU-cores per node for each cluster
# this will eventually be replaced with explicit values for each node
CORES_PER_NODE = {"adroit":32,
                  "della":28,
                  "stellar":96,
                  "tiger":40,
                  "traverse":32}
```

## Custom Job Notes

Institutions that use the Jobstats platform have the ability to write custom notes
in `config.py` that can appear at the bottom of the job efficiency reports. Here is
a simple example that makes the user aware of the Grafana dashboard:


```
                                  Notes
============================================================================
  * For additional job metrics including metrics plotted against time:
      https://mytiger.princeton.edu/pun/sys/jobstats
```

Job notes can be used to provide information and to guide users toward solving
underutilization issues such low GPU utilization or excessive CPU memory allocations.

Each note is Python code that is composed of three items: (1) a `condition`, (2) the
actual `note`, and (3) the `style`. The `condition`
is a Python string that gets evaluated to `True` or `False` when `jobstats` is ran. The `note` is
the text to be displayed. Lastly, the `style` sets the formatting which is either `normal`, `bold`, or `bold-red`.

Consider the following note in `config.py`:

```python
condition = '(self.js.cluster == "tiger")'
note = ("For additional job metrics including metrics plotted against time:",
        "https://mytiger.princeton.edu/pun/sys/jobstats")
style = "normal"
NOTES.append((condition, note, style))
```

The note above will be displayed by `jobstats` for all jobs that ran on the `tiger` cluster.

Much more sophisicated and useful notes can be constructed. For more ideas and examples, see the many notes that appear in `config.py` in the
<a href="https://github.com/PrincetonUniversity/jobstats" target="_blank">Jobstats GitHub repository</a>.

Notes can contain Slurm directives and URLs. These items are automatically
displayed on a separate line with additional indentation.

!!! warning

    System administrators should not give users the ability to add notes
    to `config.py` since in principle they could write malicious code
    that would be executed when `jobstats` is ran.

If you decide not to use notes then keep `NOTES = []` in `config.py` but remove everything 
below that line.

Below are some example notes that are possible:


```
  * This job ran on the mig partition where each job is limited to 1 MIG
    GPU, 1 CPU-core, 10 GB of GPU memory and 32 GB of CPU memory. A MIG GPU
    is about 1/7th as powerful as an A100 GPU. Please continue using the mig
    partition when possible. For more info:
      https://researchcomputing.princeton.edu/systems/della#gpus

  * This job completed while only needing 19% of the requested time which
    was 2-00:00:00. For future jobs, please decrease the value of the --time
    Slurm directive. This will lower your queue times and allow the Slurm
    job scheduler to work more effectively for all users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/slurm

  * This job did not use the GPU. Please resolve this before running
    additional jobs. Wasting resources prevents other users from getting
    their work done and it causes your subsequent jobs to have a lower
    priority. Is the code GPU-enabled? Please consult the documentation for
    the code. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing

  * This job only used 15% of the 100GB of total allocated CPU memory.
    Please consider allocating less memory by using the Slurm directive
    --mem-per-cpu=3G or --mem=18G. This will reduce your queue times and
    make the resources available to other users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/memory

  * This job ran on a large-memory (datascience) node but it only used 117
    GB of CPU memory. The large-memory nodes should only be used for jobs
    that require more than 190 GB. Please allocate less memory by using the
    Slurm directive --mem-per-cpu=9G or --mem=150G. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/memory

  * The CPU utilization of this job (24%) is approximately equal to 1
    divided by the number of allocated CPU-cores (1/4=25%). This suggests
    that you may be running a code that can only use 1 CPU-core. If this is
    true then allocating more than 1 CPU-core is wasteful. Please consult
    the documentation for the software to see if it is parallelized. For
    more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/parallel-code

  * This job did not use the CPU. This suggests that something went wrong at
    the very beginning of the job. Check your Slurm script for errors and
    look for useful information in the file slurm-46987157.out if it exists.

  * The Tiger cluster is intended for jobs that require multiple nodes. This
    job ran in the serial partition where jobs are assigned the lowest
    priority. On Tiger, a job will run in the serial partition if it only
    requires 1 node. Consider carrying out this work elsewhere.

  * For additional job metrics including metrics plotted against time:
      https://mystellar.princeton.edu/pun/sys/jobstats  (VPN required off-campus)

  * For additional job metrics including metrics plotted against time:
      https://stats.rc.princeton.edu  (VPN required off-campus)
```

Each institution that uses Jobstats is encouraged to write custom notes for their
users. We have received feedback indicating that this is one of the most useful
features of the entire Jobstats ecosystem.
