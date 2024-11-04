# Job Defense Shield

[job defense shield](https://github.com/PrincetonUniversity/job_defense_shield) - A tool for sending automated email alerts to users  

Below is an example email for automatic job cancellation:

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
Automated email alerts to users are available for these cases:

- CPU or GPU jobs with 0% utilization
- Contacting the top users with low mean CPU or GPU efficiency
- Jobs that allocate excess CPU memory (see email above)
- Serial jobs that allocate multiple CPU-cores
- Users that routinely run with excessive time limits
- Jobs that could have used a smaller number of nodes
- Jobs that could have used less powerful GPUs
- Custom email alerts are supported via the object-oriented design of the software
