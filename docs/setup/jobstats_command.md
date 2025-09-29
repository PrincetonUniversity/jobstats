# The `jobstats` command

The last step in setting up the Jobstats platform is installing the `jobstats` command. This command generates the job efficiency report. For completed jobs, the data is available in the Slurm (or MariaDB) database. For actively running jobs, the Prometheus database must be queried to obtain the data needed to generate the report.

## Installation

The installation requirements for `jobstats` are Python 3.6+, [Requests 2.20+](https://pypi.org/project/requests/) and (optionally) [blessed 1.17+](https://pypi.org/project/blessed/) which can be used for coloring and styling text. If MariaDB is used instead of the Slurm database then `mysqlclient` will be needed.

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

The four files needed to run the `jobstats` command are available in the <a href="https://github.com/PrincetonUniversity/jobstats" target="_blank">Jobstats GitHub repository</a>.

First, store the files in a path such as:

```
$ ls /usr/local/jobstats
config.py
jobstats
jobstats.py
output_formatters.py
```

Then create a symlink in `/usr/local/bin` pointing to the executable:

```
$ ln -s /usr/local/jobstats/jobstats /usr/local/bin/jobstats
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
# prometheus server address, port, and retention period
PROM_SERVER = "http://cluster-stats:8480"
PROM_RETENTION_DAYS = 365
```

`PROM_RETENTION_DAYS` is the number of days that job data will remain the Prometheus database. This is used in deciding whether to display the Grafana URL for a given job as a custom note in the `jobstats` output.

Job summary statistics can be stored in the Slurm database or one can use an external MariaDB database. By default, Slurm DB will be used:

```python
# if using Slurm database then include the lines below with "enabled": False
# if using MariaDB then set "enabled": True
EXTERNAL_DB_TABLE = "job_statistics"
EXTERNAL_DB_CONFIG = {
    "enabled": False,  # set to True to use the external db for storing stats
    "host": "127.0.0.1",
    "port": 3307,
    "database": "jobstats",
    "user": "jobstats",
    "password": "password",
#     "config_file": "/path/to/jobstats-db.cnf"
}
```

If you wish to use MariaDB then see [External Database](external-database.md).

The number of seconds between measurements by the exporters on the compute nodes:

```python
# number of seconds between measurements
SAMPLING_PERIOD = 30
```

The value above should match that in the Prometheus configuration, i.e., `scrape_interval: 30s`.

One can use the Python `blessed` package to produce bold and colorized text. This
helps to draw attention to specific lines of the report. This part
of the configuration sets the various thresholds:

```python
# threshold values for red versus black notes
GPU_UTIL_RED   = 15  # percentage
GPU_UTIL_BLACK = 25  # percentage
CPU_UTIL_RED   = 65  # percentage
CPU_UTIL_BLACK = 80  # percentage
TIME_EFFICIENCY_RED   = 10  # percentage
TIME_EFFICIENCY_BLACK = 60  # percentage
```

For instance, if the overal GPU utilization is less than 15% then it will be displayed in bold red text. Search
the conditions in the example notes in `config.py` to see how the other values are used.

The following threshold can be used to trigger notes about excessive CPU memory usage:

```python
MIN_MEMORY_USAGE = 70  # percentage
```

Notes can be suppressed if the run time of the job is less than the following threshold:

```python
MIN_RUNTIME_SECONDS = 10 * SAMPLING_PERIOD  # seconds
```

Use `CLUSTER_TRANS` to convert informal cluster names to the name that is used in the Slurm database.
For instance, if the `tiger` cluster is replaced by the `tiger2` cluster then use:

```python
CLUSTER_TRANS = {"tiger":"tiger2"}
CLUSTER_TRANS_INV = dict(zip(CLUSTER_TRANS.values(), CLUSTER_TRANS.keys()))
```

This will allow users to specify `tiger` as the cluster while internally the value `tiger2` is used
when querying the Slurm database.

One can trim long job names:

```python
# maximum number of characters to display in jobname
MAX_JOBNAME_LEN = 64
```

## MIG GPU Nodes (Optional)

At present, `jobstats` cannot report GPU utilization for NVIDIA MIG GPUs. To gracefully deal with this, specify the hostnames of your MIG GPU nodes:

```python
MIG_NODES_1 = {"della-l01g3", "della-l01g4", \
               "della-l01g5", "della-l01g6"}
MIG_NODES_2 = {"adroit-h11g2"}
```

There is no difference between `MIG_NODES_1` and `MIG_NODES_2`. The code combines them.

If MIG is not used then leave empty:

```python
MIG_NODES_1 = {}
MIG_NODES_2 = {}
```

## Custom Job Notes (Optional)

Institutions that use the Jobstats platform have the ability to write custom notes
in `config.py` that can appear at the bottom of the job efficiency reports. Here is
a simple example that makes the user aware of the Grafana dashboard:


```
                                    Notes
================================================================================
  * See the URL below for various job metrics plotted as a function of time:
      https://mytiger.princeton.edu/pun/sys/jobstats/12798795
```

Job notes can be used to provide information and to guide users toward solving
underutilization issues such low GPU utilization or excessive CPU memory allocations.

Each note is Python code that is composed of three items: (1) a `condition`, (2) the
actual `note`, and (3) the `style`. The `condition`
is a Python string that gets evaluated to `True` or `False` when `jobstats` is ran. The `note` is
the text to be displayed. Lastly, the `style` sets the formatting which is either `normal`, `bold`, or `bold-red`.

Consider the following note in `config.py`:

```python
condition = '(self.js.cluster == "tiger") and self.js.is_retained()'
note = ("See the URL below for various job metrics plotted as a function of time:",
        'f"https://mytiger.princeton.edu/pun/sys/jobstats/{self.js.jobid}"')
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
  * This job did not use the GPU. Please resolve this before running
    additional jobs. Wasting resources causes your subsequent jobs to have a
    lower priority. Is the code GPU-enabled? Please consult the documentation
    for the code. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing

  * This job used 6 GPUs from 6 compute nodes. The PLI GPU nodes on Della have
    8 GPUs per node. Please allocate all of the GPUs within a node before
    splitting your job across multiple nodes. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/slurm#gpus

  * Each node on Della (PLI) has 96 CPU-cores and 8 GPUs. If possible please
    try to allocate only up to 12 CPU-cores per GPU. This will prevent the
    situation where there are free GPUs on a node but not enough CPU-cores to
    accept new jobs. For more info:
      https://researchcomputing.princeton.edu/systems/della

  * Each node on Della (PLI) has 1024 GB of CPU memory and 8 GPUs. If possible
    please try to allocate only up to 115 GB of CPU memory per GPU. This will
    prevent the situation where there are free GPUs on a node but not enough
    CPU memory to accept new jobs. For more info:
      https://researchcomputing.princeton.edu/systems/della

  * This job ran on the mig partition where each job is limited to 1 MIG
    GPU, 1 CPU-core, 10 GB of GPU memory and 32 GB of CPU memory. A MIG GPU
    is about 1/7th as powerful as an A100 GPU. Please continue using the mig
    partition when possible. For more info:
      https://researchcomputing.princeton.edu/systems/della

  * This job should probably use a MIG GPU instead of a full A100 GPU. MIG is
    ideal for jobs with a low GPU utilization that only require a single
    CPU-core, less than 32 GB of CPU memory and less than 10 GB of GPU memory.
    For future jobs, please add the following line to your Slurm script:
      #SBATCH --partition=mig
    For more info:
      https://researchcomputing.princeton.edu/systems/della

  * This job completed while only needing 19% of the requested time which
    was 2-00:00:00. For future jobs, please decrease the value of the --time
    Slurm directive. This will lower your queue times and allow the Slurm
    job scheduler to work more effectively for all users. For more info:
      https://researchcomputing.princeton.edu/support/knowledge-base/slurm

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

  * See the URL below for various job metrics plotted as a function of time:
      https://mytiger.princeton.edu/pun/sys/jobstats/12798795
```

Each institution that uses Jobstats is encouraged to write custom notes for their
users.
