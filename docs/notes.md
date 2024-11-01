# Notes

## Custom Job Notes

The `jobstats` command analyzes each job and produces custom notes at the bottom of the output. Below are several examples:

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
