# Installing `jobstats`

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
