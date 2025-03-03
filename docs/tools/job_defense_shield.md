# Job Defense Shield

High-performance computing clusters often serve a large number of users who posses a range of knowledge and skills. This leads to individuals misusing the resources due to mistakes, misunderstandings, expediency, and related issues. To combat jobs that waste or misuse the resources, a battery of alerts can be configured. While such alerts can be configured in Prometheus, the most flexible and powerful solution is external software.

<a href="https://github.com/PrincetonUniversity/job_defense_shield" target="_blank">Job Defense Shield</a> is a Python code for sending automated email alerts to users and for creating reports for system administrators. As discussed above, summary statistics for each completed job are stored in a compressed format in the `AdminComment` field in the Slurm database. The software described here works by calling the Slurm `sacct` command while requesting several fields including `AdminComment`. The `sacct` output is stored in a `pandas` dataframe for processing.

Automated email alerts to users are available for these cases:

- CPU or GPU jobs with 0% utilization (see email below)
- Heavy users with low mean CPU or GPU efficiency
- Jobs that allocate excess CPU memory (see email below)
- Serial jobs that allocate multiple CPU-cores
- Users that routinely run with excessive time limits
- Jobs that could have used a smaller number of nodes
- Jobs that could have used less powerful GPUs
- Jobs thar ran on specialized nodes but did not need to

All of the instances in the list above can be formulated as a report
for system administrators. The most popular reports for system
administrators are:

- A list of users (and their jobs) with the most GPU-hours at 0% utilization
- A list of the heaviest users with low CPU/GPU utilization
- A list of users that are over-allocating the most CPU memory
- A list of users that are over-allocating the most time

The Python code is written using object-oriented programming techniques which makes it easy to create new alerts and reports.

# Example Report

Below is an example report of the users with the most GPU-hours at 0% utilization:

```
$ job_defense_shield --zero-util-gpu-hours

                         GPU-Hours at 0% Utilization                          
------------------------------------------------------------------------------
    User   GPU-Hours-At-0%  Jobs                 JobID                  emails
------------------------------------------------------------------------------
1  u12998        308         39   62266607,62285369,62303767,62317153+  1 (71)
2  u9l487         84         14   62301196,62301737,62301738,62301742+  0     
3  u39635         25         15   62172182,62174936,62184669,62187323+  0     
4  u24074         24         13   62303161,62303182,62303183,62303184+  0     
------------------------------------------------------------------------------
   Cluster: della
Partitions: gpu, pli-c, pli-p, pli, pli-lc
     Start: Wed Feb 12, 2025 at 09:50 AM
       End: Wed Feb 19, 2025 at 09:50 AM
```

## Example Emails

Below is an example email for the automatic cancellation of a GPU job with 0% utilization:

```
Hi Alan,

The jobs below have been cancelled because they ran for nearly 2 hours at 0% GPU
utilization:

     JobID    Cluster  Partition    State    GPUs-Allocated GPU-Util  Hours
    60131148   della      llm     CANCELLED         4          0%      2.0  
    60131741   della      llm     CANCELLED         4          0%      1.9  

See our GPU Computing webpage for three common reasons for encountering zero GPU
utilization:

    https://<your-institution>.edu/knowledge-base/gpu-computing

Replying to this automated email will open a support ticket with Research
Computing.
```

Below is an example email to a user that is requesting too much CPU memory:

```
Hi Alan,

Below are your jobs that ran on BioCluster in the past 7 days:

     JobID   Memory-Used  Memory-Allocated  Percent-Used  Cores  Hours
    5761066      2 GB          100 GB            2%         1      48
    5761091      4 GB          100 GB            4%         1      48
    5761092      3 GB          100 GB            3%         1      48

It appears that you are requesting too much CPU memory for your jobs since
you are only using on average 3% of the allocated memory. For help on
allocating CPU memory with Slurm, please see:

    https://<your-institution>.edu/knowledge-base/memory

Replying to this automated email will open a support ticket with Research
Computing. 
```

## Usage

The software has a `check` mode that shows on which days a given user received an alert of a given type. Users that appear to be ignoring the email alerts can be contacted directly. Emails to users are most effective when sent sparingly. For this reason, there is a command-line parameter to specify the amount of time that must pass before the user can receive another email of the same nature.

The example below shows how the script is called to notify users in the top N by usage with low CPU or GPU efficiencies over the last week:

```
$ job_defense_shield --low-xpu-efficiencies --days=7 --email
```

The default thresholds are 60% and 15% for CPU and GPU utilization, respectively, and N=15.

## Installation

The installation requirements for Job Defense Shield are Python 3.6+ and version 1.2+ of the Python `pandas` package. The `jobstats` command is also required if one wants to examine actively running jobs such as when looking for jobs with zero GPU utilization. The Python code, example alerts and emails, and instructions are available in the <a href="https://github.com/PrincetonUniversity/job_defense_shield" target="_blank">GitHub repository</a>.
