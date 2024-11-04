# Configuration File

Use `config.py` in the [Jobstats GitHub repository](https://github.com/PrincetonUniversity/jobstats) as the starting point for your configuration file.

Here is an explanation:

```python
# prometheus server address and port
PROM_SERVER = "http://vigilant2:8480"
```

The number of seconds between measurements by the exporters on the compute nodes:

```
# number of seconds between measurements
SAMPLING_PERIOD = 30
```

One can use the Python blessed package to produce bold and colorized text. This
helps to draw the user's attention to specific lines of the report. This part
of the configuration sets the various thresholds:

```
# threshold values for red versus black notes
GPU_UTIL_RED   = 15  # percentage
GPU_UTIL_BLACK = 25  # percentage
CPU_UTIL_RED   = 65  # percentage
CPU_UTIL_BLACK = 80  # percentage
TIME_EFFICIENCY_RED   = 40  # percentage
TIME_EFFICIENCY_BLACK = 70  # percentage
MIN_MEMORY_USAGE      = 70  # percentage
MIN_RUNTIME_SECONDS   = 10 * SAMPLING_PERIOD  # seconds
```

```
# translate cluster names in Slurm DB to informal names
CLUSTER_TRANS = {"tiger":"tiger2"}
#CLUSTER_TRANS = {}  # if no translations then use an empty dictionary
CLUSTER_TRANS_INV = dict(zip(CLUSTER_TRANS.values(), CLUSTER_TRANS.keys()))

# maximum number of characters to display in jobname
MAX_JOBNAME_LEN = 64

# default CPU memory per core in bytes for each cluster
# if unsure then use memory per node divided by cores per node
DEFAULT_MEM_PER_CORE = {"adroit":3355443200,
                        "della":4194304000,
                        "stellar":7864320000,
                        "tiger":4294967296,
                        "traverse":7812500000}

# number of CPU-cores per node for each cluster
# this will eventually be replaced with explicit values for each node
CORES_PER_NODE = {"adroit":32,
                  "della":28,
                  "stellar":96,
                  "tiger":40,
                  "traverse":32}
```
