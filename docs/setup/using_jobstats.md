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
