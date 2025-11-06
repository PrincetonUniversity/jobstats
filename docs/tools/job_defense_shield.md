# Job Defense Shield

<a href="https://princetonuniversity.github.io/job_defense_shield/" target="_blank">Job Defense Shield</a> is a software tool for identifying and reducing instances of underutilization by the users of high-performance computing systems. The software sends automated email alerts to users and creates reports for system administrators. Job Defense Shield can be used to automatically cancel GPU jobs at 0% utilization.

Below is an example report for 0% GPU utilization:

```
                         GPU-Hours at 0% Utilization
---------------------------------------------------------------------
    User   GPU-Hours-At-0%  Jobs             JobID             Emails
---------------------------------------------------------------------
1  u12998        308         39   62285369,62303767,62317153+   1 (7)
2  u9l487         84         14   62301737,62301738,62301742+   0         
3  u39635         25          2            62184669,62187323    2 (4)         
4  u24074         24         13   62303182,62303183,62303184+   0         
---------------------------------------------------------------------
   Cluster: della
Partitions: gpu, llm
     Start: Wed May 14, 2025 at 09:50 AM
       End: Wed May 21, 2025 at 09:50 AM
```

Below is an example email to a user that is requesting too much CPU memory:

```
Hi Alan (u12345),

Below are your jobs that ran on the Stellar cluster in the past 7 days:

     JobID   Memory-Used  Memory-Allocated  Percent-Used  Cores  Hours
    5761066      2 GB          100 GB            2%         1     48
    5761091      4 GB          100 GB            4%         1     48
    5761092      3 GB          100 GB            3%         1     48

It appears that you are requesting too much CPU memory for your jobs since
you are only using on average 3% of the allocated memory. For help on
allocating CPU memory with Slurm, please see:

    https://your-institution.edu/knowledge-base/memory

Replying to this automated email will open a support ticket with Research
Computing.
```
