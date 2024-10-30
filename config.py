##########################
## JOBSTATS CONFIG FILE ##
##########################

# prometheus server address and port
PROM_SERVER = "http://vigilant2:8480"

# number of seconds between measurements
SAMPLING_PERIOD = 30

# threshold values for red versus black notes
GPU_UTIL_RED   = 15  # percentage
GPU_UTIL_BLACK = 25  # percentage
CPU_UTIL_RED   = 65  # percentage
CPU_UTIL_BLACK = 80  # percentage
TIME_EFFICIENCY_RED   = 40  # percentage
TIME_EFFICIENCY_BLACK = 70  # percentage
MIN_MEMORY_USAGE      = 70  # percentage
MIN_RUNTIME_SECONDS   = 10 * SAMPLING_PERIOD  # seconds

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


#########################################################################################
##                               C U S T O M    N O T E S                              ##
##                                                                                     ##
## Be sure to work from the examples. Pay attention to the different quote characters  ##
## when f-strings are involved.                                                        ##
#########################################################################################
NOTES = []

# zero GPU utilization (single GPU jobs)
condition = 'self.js.gpus and (self.js.diff > c.MIN_RUNTIME_SECONDS) and num_unused_gpus > 0 ' \
            'and self.js.gpus == 1'
note = ("This job did not use the GPU. Please resolve this " \
        "before running additional jobs. Wasting " \
        "resources prevents other users from getting their work done " \
        "and it causes your subsequent jobs to have a lower priority. " \
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
        '"Wasting resources prevents other users from getting their work done "' \
        '"and it causes your subsequent jobs to have a lower priority. Is the "' \
        '"code capable of using multiple GPUs? Please consult the documentation for "' \
        '"the software. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing")
style = "bold-red"
NOTES.append((condition, note, style))

# low GPU utilization (ondemand and salloc)
condition = '(not zero_gpu) and self.js.gpus and (self.js.gpu_utilization <= c.GPU_UTIL_RED) ' \
            'and interactive_job and (self.js.diff / SECONDS_PER_HOUR > 12)'
note = ('f"The overall GPU utilization of this job is only {round(self.js.gpu_utilization)}%. "' \
        'f"This value is low compared to the cluster mean value of 50%. Please "' \
        'f"do not create \"salloc\" or OnDemand sessions for more than 12 hours unless you "' \
        'f"plan to work intensively during the entire period. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/gpu-computing#util")
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
condition = 'self.js.state == "OUT_OF_MEMORY"'
note = ("This job failed because it needed more CPU memory than the amount that " \
        "was requested. The solution is to resubmit the job while " \
        "requesting more CPU memory by " \
        "modifying the --mem-per-cpu or --mem Slurm directive. For more info: ",
        "https://researchcomputing.princeton.edu/support/knowledge-base/memory")
style = "bold-red"
NOTES.append((condition, note, style))

# timeout
condition = 'self.js.state == "TIMEOUT"'
note = ("This job failed because it exceeded the time limit. If there are no " \
        "other problems then the solution is to increase the value of the " \
        "--time Slurm directive and resubmit the job. For more info:",
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "bold-red"
NOTES.append((condition, note, style))

# excessive run time limit (red)
condition = 'self.js.time_eff_violation and self.js.time_efficiency <= c.TIME_EFFICIENCY_RED'
note = ('f"This job only needed {self.js.time_efficiency}% of the requested time "' \
        'f"which was {self.human_seconds(SECONDS_PER_MINUTE * self.js.timelimitraw)}. "' \
        '"For future jobs, please request less time by modifying "' \
        '"the --time Slurm directive. This will "' \
        '"lower your queue times and allow the Slurm job scheduler to work more "' \
        '"effectively for all users. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/slurm")
style = "bold-red"
NOTES.append((condition, note, style))

# excessive run time limit (black)
condition = 'self.js.time_eff_violation and self.js.time_efficiency > c.TIME_EFFICIENCY_RED'
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

# excess CPU memory
condition = '(not zero_gpu) and (not zero_cpu) and (self.js.cpu_memory_efficiency < c.MIN_MEMORY_USAGE) ' \
            'and (gb_per_core > (mpc / 1024**3) - 2) and (total > mpc) and gpu_show and ' \
            '(not self.js.partition == "datascience") and (not self.js.partition == "mig") and ' \
            '(self.js.state != "OUT_OF_MEMORY") and (cores_per_node < cpn) and ' \
            '(self.js.diff > c.MIN_RUNTIME_SECONDS)'
note = ('f"This job {opening} of the {self.cpu_memory_formatted(with_label=False)} "' \
        '"of total allocated CPU memory. "' \
        '"For future jobs, please allocate less memory by using a Slurm directive such "' \
        'f"as --mem-per-cpu={self.rounded_memory_with_safety(gb_per_core_used)}G or "' \
        'f"--mem={self.rounded_memory_with_safety(gb_per_node_used)}G. "' \
        '"This will reduce your queue times and make the resources available to "' \
        '"other users. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/memory")
style = "normal"
NOTES.append((condition, note, style))

# serial jobs wasting multiple cpu-cores
condition = '(self.js.nnodes == "1") and (int(self.js.ncpus) > 1) and (not self.js.gpus) and (serial_ratio > 0.85 ' \
            'and serial_ratio < 1.1)'
note = ('f"The CPU utilization of this job ({self.js.cpu_efficiency}%) is{approx}equal "' \
        '"to 1 divided by the number of allocated CPU-cores "' \
        'f"(1/{self.js.ncpus}={round(eff_if_serial)}%). This suggests that you may be "' \
        '"running a code that can only use 1 CPU-core. If this is true then "' \
        '"allocating more than 1 CPU-core is wasteful. Please consult the "' \
        '"documentation for the software to see if it is parallelized. For more info:"',
        "https://researchcomputing.princeton.edu/support/knowledge-base/parallel-code")
style = "normal"
NOTES.append((condition, note, style))

# job ran in the test queue
condition = '"test" in self.js.qos or "debug" in self.js.qos'
note = ('f"This job ran in the {self.js.qos} QOS. Each user can only run a small number of "' \
        '"jobs simultaneously in this QOS. For more info:"',
        'https://researchcomputing.princeton.edu/support/knowledge-base/job-priority#test-queue')
style = "normal"
NOTES.append((condition, note, style))

# more details for della
condition = '(self.js.cluster == "della")'
note = ("For additional job metrics including metrics plotted against time:",
        "https://mydella.princeton.edu/pun/sys/jobstats  (VPN required off-campus)")
style = "normal"
NOTES.append((condition, note, style))

# more details for adroit
condition = '(self.js.cluster == "adroit")'
note = ("For additional job metrics including metrics plotted against time:",
        "https://myadroit.princeton.edu/pun/sys/jobstats  (VPN required off-campus)")
style = "normal"
NOTES.append((condition, note, style))

# example of a simple note that is always displayed
condition = 'True'
note = "Have a nice day!"
style = "normal"
NOTES.append((condition, note, style))
