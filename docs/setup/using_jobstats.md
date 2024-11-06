# The `jobstats` command

For completed jobs, the data is taken from a call to sacct with several fields including AdminComment. For running jobs, the Prometheus database must be queried.

## Installation

The installation requirements for `jobstats` are Python 3.6+, [Requests 2.20+](https://pypi.org/project/requests/) and (optionally) [blessed 1.17+](https://pypi.org/project/blessed/) which can be used for coloring and styling text.

The necessary software can be installed as follows:

```bash
$ conda create --name js-env python=3.7 requests blessed -c conda-forge
```

After setting up the Jobstats platform (see below), to start using the `jobstats` command on your system, run these commands:

```bash
$ git clone https://github.com/PrincetonUniversity/jobstats.git
$ cd jobstats
# use a text editor to create config.py (see the example configuration file below)
$ chmod u+x jobstats
$ ./jobstats 1234567
```


```
$ jobstats --help
```

## Configuration File

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


## JSON Output

One can also output the raw JSON:

```
$ jobstats -j 39798795 | jq
{
  "gpus": 4,
  "nodes": {
    "della-i14g2": {
      "cpus": 24,
      "gpu_total_memory": {
        "0": 42949672960,
        "1": 42949672960
      },
      "gpu_used_memory": {
        "0": 28453568512,
        "1": 28453568512
      },
      "gpu_utilization": {
        "0": 65.7,
        "1": 64.5
      },
      "total_memory": 137438953472,
      "total_time": 164480.1,
      "used_memory": 8444272640
    },
    "della-i14g3": {
      "cpus": 24,
      "gpu_total_memory": {
        "0": 42949672960,
        "1": 42949672960
      },
      "gpu_used_memory": {
        "0": 28453634048,
        "1": 28453634048
      },
      "gpu_utilization": {
        "0": 72.9,
        "1": 67.5
      },
      "total_memory": 137438953472,
      "total_time": 154135.9,
      "used_memory": 8419606528
    }
  },
  "total_time": 67316
}
```

Use the `-b` option to generate the base64 encoded summary statistics:

```
$ jobstats -j 39798795 -b
H4sIAL25J2cC/5WQzWrEMAyE38Vn11iyJNt5mSU0ZjEkm6XrHNqQd6+T/WmzFNoeB81I82lWp7FLF9XMqkt9375koCOusoyl7Q9DGsa3d9WA8+RCZEcetZouqXuMAhGhRyGrb6GSh1QjQhSsAa1ez1O9gKTV8Twd9otnBaohjBTFY5S6w+70cg3tLs6rBwOxYwkMtRDs9D1Tcp8/2pLH0y0jbPxmFjK8VNsXs/snM9RuwhiemJnAsYm/MdsnZvgD851RHFkK+vGDq/6ZeUX1hjezRxOXFfp7YfEOZIvWtrR8AhsXFkMPAgAA
```
