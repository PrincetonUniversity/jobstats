##########################
## JOBSTATS CONFIG FILE ##
##########################

# prometheus server address, port, and retention period
PROM_SERVER = "http://cluster-stats:8480"
PROM_RETENTION_DAYS = 365

# if using Slurm database then include the lines below with "enabled": False
# if using MariaDB then set "enabled": True and uncomment "config_file"
EXTERNAL_DB_CONFIG = {
    "enabled": False,  # set to True to use the external db for storing stats
    "host": "127.0.0.1",
    "port": 3307,
    "database": "jobstats",
    "user": "jobstats",
    "password": "password",
#     "config_file": "/path/to/jobstats-db.cnf"
}

# number of seconds between measurements
SAMPLING_PERIOD = 30

# threshold values for red versus black text and notes
GPU_UTIL_RED   = 15  # percentage
GPU_UTIL_BLACK = 25  # percentage
CPU_UTIL_RED   = 65  # percentage
CPU_UTIL_BLACK = 80  # percentage
TIME_EFFICIENCY_RED   = 10  # percentage
TIME_EFFICIENCY_BLACK = 60  # percentage
MIN_MEMORY_USAGE      = 70  # percentage
MIN_RUNTIME_SECONDS   = 10 * SAMPLING_PERIOD  # seconds

# translate cluster names in Slurm DB to informal names
CLUSTER_TRANS = {}  # if no translations then use an empty dictionary
CLUSTER_TRANS_INV = dict(zip(CLUSTER_TRANS.values(), CLUSTER_TRANS.keys()))

# maximum number of characters to display in jobname
MAX_JOBNAME_LEN = 64


################################################################################
##                         C U S T O M    N O T E S                           ##
##                                                                            ##
##  Be sure to work from the examples. Pay attention to the different quote   ##
##  characters when f-strings are involved.                                   ##
################################################################################

NOTES = []

###############################
# B O L D   R E D   N O T E S #
###############################

# zero GPU utilization (single GPU jobs)
condition = 'self.js.gpus and (self.js.diff > c.MIN_RUNTIME_SECONDS) and num_unused_gpus > 0 ' \
            'and self.js.gpus == 1'
note = ("This job did not use the GPU. Please resolve this " \
        "before running additional jobs. Wasting resources " \
        "will cause your subsequent jobs to have a lower priority. " \
        "Is the code GPU-enabled? " \
        "Please consult the documentation for the software. For more info:",
        "https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing")
style = "bold-red"
NOTES.append((condition, note, style))

# zero GPU utilization (multi-GPU jobs)
condition = 'self.js.gpus and (self.js.diff > c.MIN_RUNTIME_SECONDS) and num_unused_gpus > 0 ' \
            'and self.js.gpus > 1'
note = ('f"This job did not use {num_unused_gpus} of the {self.js.gpus} allocated GPUs. "' \
        '"Please resolve this before running additional jobs. "' \
        'f"Wasting resources will cause your subsequent jobs to have a lower priority. {multi}"' \
        '"Please consult the documentation for the software. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing")
style = "bold-red"
NOTES.append((condition, note, style))

# zero CPU utilization (single node)
condition = '(self.js.diff > c.MIN_RUNTIME_SECONDS) and (num_unused_nodes > 0) ' \
            'and (self.js.nnodes == "1")'
note = ('"This job did not use the CPU. This suggests that something went wrong "' \
        '"at the very beginning of the job. For batch jobs, check your Slurm and "' \
        '"application scripts for errors and look for useful information in the "' \
        'f"file slurm-{self.js.jobid}.out if it exists."')
style = "bold-red"
NOTES.append((condition, note, style))

# zero CPU utilization (multiple nodes)
condition = '(self.js.diff > c.MIN_RUNTIME_SECONDS) and (num_unused_nodes > 0) ' \
            'and (int(self.js.nnodes) > 1)'
note = ('f"This job did not use {num_unused_nodes} of the {self.js.nnodes} allocated "' \
        'f"nodes. Please resolve this before running additional jobs. {multi_cpu}Please "' \
        '"consult the documentation for the software. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/parallel-code")
style = "bold-red"
NOTES.append((condition, note, style))

# jobs that should have used 10 GB MIG (batch jobs)
condition = '(not zero_gpu) and (self.js.gpus == 1) and (self.js.cluster == "della") and ' \
            '(self.js.partition == "gpu") and (self.js.diff > c.MIN_RUNTIME_SECONDS) and ' \
            '(self.js.gpu_utilization < c.GPU_UTIL_RED) and (int(self.js.ncpus) == 1) and ' \
            '(gb_per_node_used < 32) and (gpu_mem_used < 10) and ' \
            '(self.js.jobname != "interactive") and ' \
            '(not self.js.jobname.startswith("sys/dashboard/sys/jupyter"))'
note = ("This job should probably use a 10 GB MIG GPU instead of a full A100 GPU. MIG is " \
        "ideal for jobs with a low GPU utilization that only require a single CPU-core, " \
        "less than 32 GB of CPU memory, and less than 10 GB of GPU memory. For " \
        "future jobs, please add the following line to your Slurm script:",
        "#SBATCH --partition=mig",
        "For more info:",
        "https://researchcomputing.princeton.edu/systems/della#gpus")
style = "bold-red"
NOTES.append((condition, note, style))

# jobs that should have used 10 GB MIG (salloc jobs)
condition = '(not zero_gpu) and (self.js.gpus == 1) and (self.js.cluster == "della") and ' \
            '(self.js.partition in ["gpu", "gputest"]) and (self.js.diff > c.MIN_RUNTIME_SECONDS) and ' \
            '(self.js.gpu_utilization < c.GPU_UTIL_RED) and (int(self.js.ncpus) == 1) and ' \
            '(gb_per_node_used < 32) and (gpu_mem_used < 10) and ' \
            '(self.js.jobname == "interactive")'
note = ("This job should probably use a 10 GB MIG GPU instead of a full A100 GPU. MIG is " \
        "ideal for jobs with a low GPU utilization that only require a single CPU-core, " \
        "less than 32 GB of CPU memory, and less than 10 GB of GPU memory. To use MIG " \
        "with \"salloc\":",
        "$ salloc --nodes=1 --ntasks=1 --time=60:00 --gres=gpu:1 --partition=mig",
        "For more info:",
        "https://researchcomputing.princeton.edu/systems/della#gpus")
style = "bold-red"
NOTES.append((condition, note, style))

# jobs that should have used 10 GB MIG (jupyter ondemand jobs)
condition = '(not zero_gpu) and (self.js.gpus == 1) and (self.js.cluster == "della") and ' \
            '(self.js.partition in ["gpu", "gputest"]) and (self.js.diff > c.MIN_RUNTIME_SECONDS) and ' \
            '(self.js.gpu_utilization < c.GPU_UTIL_RED) and (int(self.js.ncpus) == 1) and ' \
            '(gb_per_node_used < 32) and (gpu_mem_used < 10) and ' \
            '(self.js.jobname.startswith("sys/dashboard/sys/jupyter"))'
note = ("This job should probably use a 10 GB MIG GPU instead of a full A100 GPU. MIG is " \
        "ideal for jobs with a low GPU utilization that only require a single CPU-core, " \
        "less than 32 GB of CPU memory, and less than 10 GB of GPU memory. To use MIG " \
        "with OnDemand Jupyter, choose \"mig\" as the \"Custom partition\" when " \
        "creating the session. For more info:",
        "https://researchcomputing.princeton.edu/support/knowledge-base/jupyter#environments")
style = "bold-red"
NOTES.append((condition, note, style))

# low GPU utilization (ondemand and salloc)
condition = '(not zero_gpu) and self.js.gpus and (self.js.gpu_utilization <= c.GPU_UTIL_RED) ' \
            'and interactive_job and (self.js.diff / SECONDS_PER_HOUR > 8)'
note = ('f"The overall GPU utilization of this job is only {round(self.js.gpu_utilization)}%. "' \
        '"This value is low compared to the cluster mean value of 50%. Please "' \
        '"do not create \'salloc\' or OnDemand sessions for more than 8 hours unless you "' \
        '"plan to work intensively during the entire period."')
style = "bold-red"
NOTES.append((condition, note, style))

# low GPU utilization (batch jobs)
condition = '(not zero_gpu) and self.js.gpus and (self.js.gpu_utilization <= c.GPU_UTIL_RED) ' \
            'and (not interactive_job)'
note = ('f"The overall GPU utilization of this job is only {round(self.js.gpu_utilization)}%. "' \
        '"This value is low compared to the cluster mean value of 50%. Please "' \
        '"investigate the reason for the low utilization. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing#util")
style = "bold-red"
NOTES.append((condition, note, style))

# low CPU utilization (red, more than one core)
condition = '(not zero_cpu) and (not self.js.gpus) and (self.js.cpu_efficiency < c.CPU_UTIL_RED) ' \
            'and (int(self.js.ncpus) > 1)'
note = ('f"The overall CPU utilization of this job is {ceff}%. This value "' \
        'f"is{somewhat}low compared to the target range of "' \
        'f"90% and above. Please investigate the reason for the low efficiency. "' \
        '"For instance, have you conducted a scaling analysis? For more info:"',
        "https://researchcomputing.princeton.edu/get-started/cpu-utilization")
style = "bold-red"
NOTES.append((condition, note, style))

# low CPU utilization (red, serial job)
condition = '(not zero_cpu) and (not self.js.gpus) and (self.js.cpu_efficiency < c.CPU_UTIL_RED) ' \
            'and (int(self.js.ncpus) == 1)'
note = ('f"The overall CPU utilization of this job is {ceff}%. This value "' \
        'f"is{somewhat}low compared to the target range of "' \
        'f"90% and above. Please investigate the reason for the low efficiency. "' \
        '"For more info:"',
        "https://researchcomputing.princeton.edu/get-started/cpu-utilization")
style = "bold-red"
NOTES.append((condition, note, style))

# out of memory
condition = 'self.js.state == "OUT_OF_MEMORY" and (not zero_cpu)'
note = ("This job failed because it needed more CPU memory than the amount that " \
        "was requested. If there are no other problems then the solution is to " \
        "resubmit the job while requesting more CPU memory by " \
        "modifying the --mem-per-cpu or --mem Slurm directive. For more info: ",
        "https://researchcomputing.princeton.edu/support/knowledge-base/memory")
style = "bold-red"
NOTES.append((condition, note, style))

# timeout
condition = '(self.js.state == "TIMEOUT") and (not zero_gpu) and (not zero_cpu)'
note = ("This job failed because it exceeded the time limit. If there are no " \
        "other problems then the solution is to increase the value of the " \
        "--time Slurm directive and resubmit the job. For more info:",
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "bold-red"
NOTES.append((condition, note, style))

# excessive run time limit (red)
condition = 'self.js.time_eff_violation and self.js.time_efficiency <= c.TIME_EFFICIENCY_RED ' \
            'and (not zero_gpu) and (not zero_cpu)'
note = ('f"This job only needed {self.js.time_efficiency}% of the requested time "' \
        'f"which was {self.human_seconds(SECONDS_PER_MINUTE * self.js.timelimitraw)}. "' \
        '"For future jobs, please request less time by modifying "' \
        '"the --time Slurm directive. This will "' \
        '"lower your queue times and allow the Slurm job scheduler to work more "' \
        '"effectively for all users. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "bold-red"
NOTES.append((condition, note, style))

#########################
# P L A I N   N O T E S #
#########################

# excessive run time limit (black)
condition = 'self.js.time_eff_violation and self.js.time_efficiency > c.TIME_EFFICIENCY_RED ' \
            'and (not zero_gpu) and (not zero_cpu)'
note = ('f"This job only needed {self.js.time_efficiency}% of the requested time "' \
        'f"which was {self.human_seconds(SECONDS_PER_MINUTE * self.js.timelimitraw)}. "' \
        '"For future jobs, please request less time by modifying "' \
        '"the --time Slurm directive. This will "' \
        '"lower your queue times and allow the Slurm job scheduler to work more "' \
        '"effectively for all users. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "normal"
NOTES.append((condition, note, style))

# somewhat low GPU utilization
condition = '(not zero_gpu) and self.js.gpus and (self.js.gpu_utilization < c.GPU_UTIL_BLACK) and ' \
            '(self.js.gpu_utilization > c.GPU_UTIL_RED) and (self.js.diff > c.MIN_RUNTIME_SECONDS)'
note = ('f"The overall GPU utilization of this job is {round(self.js.gpu_utilization)}%. "' \
        '"This value is somewhat low compared to the cluster mean value of 50%. For more info:"',
        'https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing#util')
style = "normal"
NOTES.append((condition, note, style))

# low CPU utilization (black, more than one core)
condition = '(not zero_cpu) and (not self.js.gpus) and (self.js.cpu_efficiency <= c.CPU_UTIL_BLACK) ' \
            'and (self.js.cpu_efficiency > c.CPU_UTIL_RED) and int(self.js.ncpus) > 1'
note = ('f"The overall CPU utilization of this job is {ceff}%. This value "' \
        'f"is{somewhat}low compared to the target range of "' \
        'f"90% and above. Please investigate the reason for the low efficiency. "' \
        '"For instance, have you conducted a scaling analysis? For more info:"',
        "https://researchcomputing.princeton.edu/get-started/cpu-utilization")
style = "normal"
NOTES.append((condition, note, style))

# low CPU utilization (black, serial job)
condition = '(not zero_cpu) and (not self.js.gpus) and (self.js.cpu_efficiency <= c.CPU_UTIL_BLACK) ' \
            'and (self.js.cpu_efficiency > c.CPU_UTIL_RED) and int(self.js.ncpus) == 1'
note = ('f"The overall CPU utilization of this job is {ceff}%. This value "' \
        'f"is{somewhat}low compared to the target range of "' \
        'f"90% and above. Please investigate the reason for the low efficiency. "' \
        '"For more info:"',
        "https://researchcomputing.princeton.edu/get-started/cpu-utilization")
style = "normal"
NOTES.append((condition, note, style))

# CPU job that used too many nodes or too few cores per node (ignoring GPU jobs)
condition = '(int(self.js.nnodes) > 1) and (not self.js.gpus) and (self.js.cluster == "della") ' \
            'and (cores_per_node < 16) and (gb_per_node_used < 0.85 * 190 / int(self.js.nnodes))'
note = ('f"This job used {self.js.ncpus} CPU-cores from {self.js.nnodes} compute "' \
        '"nodes. Please try to use as few nodes as possible by decreasing "' \
        '"the value of the --nodes Slurm directive and increasing the value of --ntasks-per-node. "' \
        '"Run the \'shownodes\' command to see the number of "' \
        '"CPU-cores per node (see \'TOTAL CPUs\' column). Della has nodes with 192 "' \
        '"CPU-cores and 1 TB of memory. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "normal"
NOTES.append((condition, note, style))

condition = '(int(self.js.nnodes) > 1) and (not self.js.gpus) and (self.js.cluster == "stellar") ' \
            'and (cores_per_node < 48) and (gb_per_node_used < 0.85 * 512 / int(self.js.nnodes))'
note = ('f"This job used {self.js.ncpus} CPU-cores from {self.js.nnodes} compute "' \
        '"nodes. Please try to use as few nodes as possible by decreasing "' \
        '"the value of the --nodes Slurm directive and increasing the value of --ntasks-per-node. "' \
        '"Each Intel node (PU, PPPL) provides 96 CPU-cores and 760 GB of memory while "' \
        '"an AMD node (CIMES) offers 128 cores and 512 GB. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "normal"
NOTES.append((condition, note, style))

condition = '(int(self.js.nnodes) > 1) and (not self.js.gpus) and (self.js.cluster == "tiger3") ' \
            'and (cores_per_node < 56) and (gb_per_node_used < 0.85 * 1000 / int(self.js.nnodes))'
note = ('f"This job used {self.js.ncpus} CPU-cores from {self.js.nnodes} compute "' \
        '"nodes. Please try to use as few nodes as possible by decreasing "' \
        '"the value of the --nodes Slurm directive and increasing the value of --ntasks-per-node. "' \
        '"Each Tiger (CPU) node provides 112 CPU-cores and 1000 GB of memory. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "normal"
NOTES.append((condition, note, style))

condition = '(int(self.js.nnodes) > 1) and (not self.js.gpus) and (self.js.cluster == "adroit") ' \
            'and (cores_per_node < 16) and (gb_per_node_used < 0.85 * 384 / int(self.js.nnodes))'
note = ('f"This job used {self.js.ncpus} CPU-cores from {self.js.nnodes} compute "' \
        '"nodes. Please try to use as few nodes as possible by decreasing "' \
        '"the value of the --nodes Slurm directive and increasing the value of --ntasks-per-node. "' \
        '"Run the \'shownodes\' command to see the number of "' \
        '"CPU-cores per node (see \'TOTAL CPUs\' column). For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "normal"
NOTES.append((condition, note, style))

# multinode GPU fragmentation
condition = '(int(self.js.nnodes) > 1) and self.js.gpus and (self.js.cluster == "della") and ' \
            '(int(self.js.nnodes) == self.js.gpus) and ("pli" not in self.js.partition)'
note = ('f"This job used {self.js.gpus} GPUs from {self.js.nnodes} compute nodes. "' \
        '"The nodes on the \'gpu\' partition of Della have either 2 or 4 GPUs per node. Please "' \
        '"try to use as few nodes as possible by lowering the value of the "' \
        '"--nodes Slurm directive and increasing the value of --gres=gpu:<N>. "' \
        '"For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm#gpus")
style = "normal"
NOTES.append((condition, note, style))

condition = '(self.js.cluster == "della") and ("pli" in self.js.partition) and ' \
            '(int(self.js.nnodes) > 1) and (self.js.gpus / int(self.js.nnodes) < 8) '
note = ('f"This job used {self.js.gpus} GPUs from {self.js.nnodes} compute nodes. "' \
        '"The PLI GPU nodes on Della have 8 GPUs per node. Please allocate "' \
        '"all of the GPUs within a node before splitting your job across "' \
        '"multiple nodes. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm#gpus")
style = "normal"
NOTES.append((condition, note, style))

condition = '(self.js.cluster == "tiger3") and (self.js.partition == "gpu") and ' \
            '(int(self.js.nnodes) > 1) and (self.js.gpus / int(self.js.nnodes) < 4) '
note = ('f"This job used {self.js.gpus} GPUs from {self.js.nnodes} compute nodes. "' \
        '"The H100 GPU nodes on Tiger have 4 GPUs per node. Please allocate "' \
        '"all of the GPUs within a node before splitting your job across "' \
        '"multiple nodes. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm#gpus")
style = "normal"
NOTES.append((condition, note, style))

# too many CPU-cores per GPU
condition = '(self.js.cluster == "della") and ("pli" in self.js.partition) and ' \
            '(not zero_gpu) and (cores_per_gpu > 12)'
note = ("Each node on Della (PLI) has 96 CPU-cores and 8 GPUs. If possible " \
        "please try to allocate only up to 12 CPU-cores per GPU. This will " \
        "prevent the situation where there are free GPUs on a node but not " \
        "enough CPU-cores to accept new jobs. For more info:",
        "https://researchcomputing.princeton.edu/systems/della#pli")
style = "normal"
NOTES.append((condition, note, style))

condition = '(self.js.cluster == "tiger3") and (self.js.partition == "gpu") and ' \
            '(not zero_gpu) and (cores_per_gpu > 12)'
note = ("Each node on Tiger (gpu) has 112 CPU-cores and 4 GPUs. If possible " \
        "please try to allocate only up to 12 CPU-cores per GPU. This will " \
        "prevent the situation where there are free GPUs on a node but not " \
        "enough CPU-cores to accept new jobs. For more info:",
        "https://researchcomputing.princeton.edu/systems/tiger")
style = "normal"
NOTES.append((condition, note, style))

# too much CPU memory per GPU
condition = '(self.js.cluster == "della") and ("pli" in self.js.partition) and ' \
            '(not zero_gpu) and (cpu_mem_per_gpu > 115) and (total_used / total < 0.85)'
note = ("Each node on Della (PLI) has 1024 GB of CPU memory " \
        "and 8 GPUs. If possible please try to allocate only up to 115 GB of " \
        "CPU memory per GPU. This will prevent the situation where there " \
        "are free GPUs on a node but not enough CPU memory to accept new " \
        "jobs. For more info:",
        "https://researchcomputing.princeton.edu/systems/della#pli")
style = "normal"
NOTES.append((condition, note, style))

condition = '(self.js.cluster == "tiger3") and (self.js.partition == "gpu") and ' \
            '(not zero_gpu) and (cpu_mem_per_gpu > 240) and (total_used / total < 0.85)'
note = ("Each node on Tiger (gpu) has 1000 GB of CPU memory " \
        "and 4 GPUs. If possible please try to allocate only up to 240 GB of " \
        "CPU memory per GPU. This will prevent the situation where there " \
        "are free GPUs on a node but not enough CPU memory to accept new " \
        "jobs. For more info:",
        "https://researchcomputing.princeton.edu/systems/tiger")
style = "normal"
NOTES.append((condition, note, style))

# overallocating CPU memory (for CPU and GPU jobs)
"""Ignore jobs that use the default memory per core and jobs that almost allocate
   all of the CPU-cores. Also ignore GPU jobs that allocate less than 50 GB of
   CPU memory per GPU (would also be nice to ignore jobs that allocate all of the
   GPUs per node). DEFAULT_MEM_PER_CORE is the default CPU memory per core in
   bytes. If unsure what to use for this then use the memory per node divided by
   the number of cores per node."""
DEFAULT_MEM_PER_CORE = {"adroit":  3_300_000_000,
                        "della":   4_100_000_000,
                        "stellar": 7_600_000_000,
                        "tiger3":  8_100_000_000}
CORES_PER_NODE = {"adroit":64,
                  "della":192,
                  "stellar":96,
                  "tiger":112}
condition = '(not zero_gpu) and (not zero_cpu) and (self.js.cpu_memory_efficiency < c.MIN_MEMORY_USAGE) ' \
            'and (gb_per_core_total > mpc / 1024**3) and gpu_show and (not self.js.partition == "mig") and ' \
            '(self.js.state != "OUT_OF_MEMORY") and (cores_per_node < 0.85 * cpn) and ' \
            '(self.js.diff > c.MIN_RUNTIME_SECONDS)'
note = ('f"This job {opening} of the {self.cpu_memory_formatted(with_label=False)} "' \
        '"of total allocated CPU memory. "' \
        '"For future jobs, please allocate less memory by using a Slurm directive such "' \
        'f"as --mem-per-cpu={self.rounded_memory_with_safety(gb_per_core_used)}G or "' \
        'f"--mem={self.rounded_memory_with_safety(gb_per_node_used)}G. "' \
        '"This will reduce your queue times and make the resources available to "' \
        '"other jobs. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/memory")
style = "normal"
NOTES.append((condition, note, style))

# serial jobs wasting multiple CPU-cores
condition = '(self.js.nnodes == "1") and (int(self.js.ncpus) > 1) and (not self.js.gpus) and ' \
            '(serial_ratio > 0.85 and serial_ratio < 1.01)'
note = ('f"The CPU utilization of this job ({self.js.cpu_efficiency}%) is{approx}equal "' \
        '"to 1 divided by the number of allocated CPU-cores "' \
        'f"(1/{self.js.ncpus}={round(eff_if_serial, 1)}%). This suggests that you may be "' \
        '"running a code that can only use 1 CPU-core. If this is true then "' \
        '"allocating more than 1 CPU-core is wasteful. Please consult the "' \
        '"documentation for the software to see if it is parallelized. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/parallel-code")
style = "normal"
NOTES.append((condition, note, style))

# jobs using less than half of a node on the Stellar cluster
condition = '(self.js.nnodes == "1") and (self.js.cluster == "stellar") and (not self.js.gpus) and ' \
            '(int(self.js.ncpus) < 48) and (not self.js.qos == "stellar-debug")'
note = ("The Stellar cluster is intended for jobs that require " \
        "multiple nodes. This job ran in the \"serial\" partition where jobs are " \
        "assigned the lowest priority. On Stellar, a job will run in the \"serial\" " \
        "partition if it requires 1 node and less than 48 CPU-cores. " \
        "Please consider carrying out this work elsewhere.")
style = "normal"
NOTES.append((condition, note, style))

# job ran using 40GB MIG GPU
MIG_NODES_1 = {"della-l01g3", "della-l01g4", "della-l01g5", "della-l01g6", "della-l01g7",
               "della-l01g8", "della-l01g9", "della-l01g10", "della-l01g11", "della-l01g12",
               "adroit-h11g2"}
condition = 'self.js.cluster == "della" and self.js.partition in ("gpu", "gputest") ' \
            'and self.js.is_mig_job()'
note = ("This job used a 40GB MIG GPU which work well for almost all codes. " \
        "A 40GB MIG GPU has half the compute power of a full A100 GPU. If " \
        "a full A100 is needed or if you suspect that MIG is causing problems " \
        "then see \"nomig\" on this webpage:",
        "https://researchcomputing.princeton.edu/systems/della#gpus")
style = "normal"
NOTES.append((condition, note, style))

# job ran using 10GB MIG GPU
MIG_NODES_2 = {"della-l01g1", "della-l01g2"}
condition = 'self.js.cluster == "della" and self.js.partition == "mig"'
note = ("This job ran on the \"mig\" partition where each job is limited to 1 MIG GPU, " \
        "1 CPU-core, 10 GB of GPU memory and 32 GB of CPU memory. A MIG GPU is " \
        "about 1/7th as powerful as an A100 GPU. Please continue to use the \"mig\" partition. " \
        "For more info:",
        'https://researchcomputing.princeton.edu/systems/della#gpus')
style = "normal"
NOTES.append((condition, note, style))

# job ran in the test queue
condition = '("test" in self.js.qos) or ("debug" in self.js.qos)'
note = ('f"This job ran in the {self.js.qos} QOS. Each user can only run a small number of "' \
        '"jobs simultaneously in this QOS. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/job-priority#test-queue")
style = "normal"
NOTES.append((condition, note, style))

# grafana URL via Open OnDemand helper app for Adroit cluster
condition = '(self.js.cluster == "adroit") and self.js.is_retained()'
note = ("See the URL below for various job metrics plotted as a function of time:",
        'f"https://myadroit.princeton.edu/pun/sys/jobstats/{self.js.jobid}  (VPN required off-campus)"')
style = "normal"
NOTES.append((condition, note, style))

# grafana URL via Open OnDemand helper app for Della cluster
condition = '(self.js.cluster == "della") and self.js.is_retained()'
note = ("See the URL below for various job metrics plotted as a function of time:",
        'f"https://mydella.princeton.edu/pun/sys/jobstats/{self.js.jobid}  (VPN required off-campus)"')
style = "normal"
NOTES.append((condition, note, style))

# grafana URL via Open OnDemand helper app for Stellar cluster
condition = '(self.js.cluster == "stellar") and self.js.is_retained()'
note = ("See the URL below for various job metrics plotted as a function of time:",
        'f"https://mystellar.princeton.edu/pun/sys/jobstats/{self.js.jobid}  (VPN required off-campus)"')
style = "normal"
NOTES.append((condition, note, style))

# grafana URL via Open OnDemand helper app for Tiger cluster
condition = '(self.js.cluster == "tiger") and self.js.is_retained()'
note = ("See the URL below for various job metrics plotted as a function of time:",
        'f"https://mytiger.princeton.edu/pun/sys/jobstats/{self.js.jobid}  (VPN required off-campus)"')
style = "normal"
NOTES.append((condition, note, style))

# example of a simple note that is always displayed
condition = 'True'
note = "Have a nice day!"
style = "normal"
NOTES.append((condition, note, style))
