import math
import datetime
from abc import ABC, abstractmethod
from textwrap import TextWrapper
import config as c
from jobstats import Jobstats
try:
    from blessed import Terminal
    blessed_is_available = True
except ModuleNotFoundError:
    blessed_is_available = False


# conversion factors
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600


class BaseFormatter(ABC):
    """Abstract base class for custom output formatters. An output
       formatter is used to print the job report."""

    def __init__(self, js: Jobstats) -> None:
        self.js = js

    @abstractmethod
    def output(self, no_color: bool=True) -> str:
        pass

    @staticmethod
    def human_bytes(size, decimal_places=1):
        size = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                break
            size /= 1024
        return f"{size:.{decimal_places}f}{unit}"

    @staticmethod
    def human_seconds(seconds):
        hour = seconds // 3600
        if hour >= 24:
            days = "%d-" % (hour // 24)
            hour %= 24
            hour = days + ("%02d:" % hour)
        else:
            if hour > 0:
                hour = "%02d:" % hour
            else:
                hour = '00:'
        seconds = seconds % (24 * 3600)
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return "%s%02d:%02d" % (hour, minutes, seconds)

    @staticmethod
    def human_datetime(seconds_since_epoch):
       fmt = "%a %b %-d, %Y at %-I:%M %p"
       return datetime.datetime.fromtimestamp(seconds_since_epoch).strftime(fmt)

    def cpu_memory_formatted(self, with_label=True):
        total = self.js.reqmem.replace("000M", "G").replace("000G", "T").replace(".50G", ".5G").replace(".50T", ".5T")
        if (int(self.js.ncpus) == 1 or all([X not in total for X in ("K", "M", "G", "T")])) and with_label:
            return f'     CPU Memory: {total.replace("M", "MB").replace("G", "GB").replace("T", "TB")}'
        if total.endswith("K"):
            bytes_ = float(total.replace("K", "")) * 1e3
        elif total.endswith("M"):
            bytes_ = float(total.replace("M", "")) * 1e6
        elif total.endswith("G"):
            bytes_ = float(total.replace("G", "")) * 1e9
        elif total.endswith("T"):
            bytes_ = float(total.replace("T", "")) * 1e12
        else:
            return total
        bytes_per_core = bytes_ / int(self.js.ncpus)
        for unit in ['B','KB', 'MB', 'GB', 'TB']:
            if bytes_per_core < 1000:
                break
            bytes_per_core /= 1000
        bpc = f"{bytes_per_core:.1f}"
        bpc = bpc.replace(".0", "")
        ttl = total.replace("M", "MB").replace("G", "GB").replace("T", "TB")
        if with_label:
            return f'     CPU Memory: {ttl} ({bpc}{unit} per CPU-core)'
        else:
            return ttl
 
    @staticmethod
    def rounded_memory_with_safety(mem_used: float) -> int:
        """Return a rounded version of the suggested memory including 20% safety."""
        mem_with_safety = math.ceil(1.2 * mem_used)
        if mem_with_safety > 1000:
            mem_suggested = round(mem_with_safety, -2)
            if mem_suggested - mem_with_safety < 0:
                mem_suggested += 100
        elif mem_with_safety > 100:
            mem_suggested = round(mem_with_safety, -1)
            if mem_suggested - mem_with_safety < 0:
                mem_suggested += 10
        elif mem_with_safety > 30:
            mem_suggested = round(mem_with_safety, -1)
            if mem_suggested - mem_with_safety < 0:
                mem_suggested += 5
        else:
            return max(1, mem_with_safety)
        return mem_suggested

    def time_limit_formatted(self):
        self.js.time_eff_violation = False
        clr = self.txt_normal
        if self.js.state == "COMPLETED" and self.js.timelimitraw > 0:
            self.js.time_efficiency = round(100 * self.js.diff / (SECONDS_PER_MINUTE * self.js.timelimitraw))
            if self.js.time_efficiency > 100:
                self.js.time_efficiency = 100
            if self.js.time_efficiency < c.TIME_EFFICIENCY_BLACK and self.js.diff > 3 * c.MIN_RUNTIME_SECONDS:
                self.js.time_eff_violation = True
            if self.js.time_efficiency < c.TIME_EFFICIENCY_RED and self.js.time_eff_violation:
                clr = f"{self.txt_bold}{self.txt_red}"
        hs = self.human_seconds(SECONDS_PER_MINUTE * self.js.timelimitraw)
        return f"     Time Limit: {clr}{hs}{self.txt_normal}"

    def draw_meter(self, efficiency, hardware, util=False):
        bars = efficiency // 2
        if bars < 0:
            bars = 0
        elif bars > 50:
            bars = 50
        text = f"{efficiency}%"
        spaces = 50 - bars - len(text)
        if bars + len(text) > 50:
            bars = 50 - len(text)
            spaces = 0
        clr1 = ""
        clr2 = ""
        if (efficiency < c.CPU_UTIL_RED and hardware == "cpu" and util and (not self.js.gpus)) or \
           (efficiency < c.GPU_UTIL_RED and hardware == "gpu" and util):
            clr1 = f"{self.txt_red}"
            clr2 = f"{self.txt_bold}{self.txt_red}"
        return f"{self.txt_bold}[{self.txt_normal}" + clr1 + bars * "|" + spaces * " " + clr2 + \
               text + f"{self.txt_normal}{self.txt_bold}]{self.txt_normal}"

    def format_note(self, *items, style="normal", indent_width=4, bullet="*") -> str:
        """Combine the pieces of the note and apply formatting."""
        indent = " " * indent_width
        first_indent = [" " for _ in range(indent_width)]
        if len(first_indent) >= 2:
            first_indent[-2] = bullet
        first_indent = "".join(first_indent)
        wrapper = TextWrapper(width=78,
                              subsequent_indent=indent,
                              break_on_hyphens=False)
        # combine the parts of the note
        note = ""
        starts = ("http", "ftp", "$ ", "#SBATCH")
        for i, item in enumerate(items):
            if i == 0:
                wrapper.initial_indent = first_indent
                note += wrapper.fill(item)
            elif any([item.startswith(start) for start in starts]):
                note += f"\n{indent}  {item}\n"
            elif item == "\n":
                note += item
            else:
                wrapper.initial_indent = indent
                note += wrapper.fill(item)
        # apply styling
        if style == "bold":
            styling = self.txt_bold
        elif style == "bold-red":
            styling = f"{self.txt_bold}{self.txt_red}"
        else:
            styling = ""
        # add newline(s) to the end of the note
        if any([items[-1].startswith(start) for start in starts]):
            newlines = "\n"
        else:
            newlines = "\n\n"
        return f"{styling}{note}{self.txt_normal}{newlines}"

    def job_notes(self):
        s = ""
        # compute several quantities which can then referenced in notes
        total_used, total, total_cores = self.js.cpu_mem_total__used_alloc_cores
        cores_per_node = int(self.js.ncpus) / int(self.js.nnodes)
        gb_per_core_used = total_used / total_cores / 1024**3 if total_cores != 0 else 0
        gb_per_node_used = total_used / int(self.js.nnodes) / 1024**3 if int(self.js.nnodes) != 0 else 0
        # zero GPU/CPU utilization
        if self.js.gpus:
            num_unused_gpus = sum([util == 0 for _, util, _ in self.js.gpu_util__node_util_index])
        else:
            num_unused_gpus = 0
        zero_gpu = False  # unused
        zero_cpu = False  # unused
        gpu_show = True   # unused
        # low GPU utilization
        interactive_job = "sys/dashboard/sys/" in self.js.jobname or self.js.jobname == "interactive"
        # low cpu utilization
        somewhat = " " if self.js.cpu_efficiency < c.CPU_UTIL_RED else " somewhat "
        ceff = self.js.cpu_efficiency if self.js.cpu_efficiency > 0 else "less than 1"
        # next three lines needed for serial code using multiple CPU-cores note
        eff_if_serial = 100 / int(self.js.ncpus) if self.js.ncpus != "0" else -1
        serial_ratio = self.js.cpu_efficiency / eff_if_serial
        approx = " approximately " if self.js.cpu_efficiency != round(eff_if_serial) else " "
        # next four lines needed for excess CPU memory note
        cpu_memory_utilization = round(100 * total_used / total) if total != 0 else 0
        gb_per_core = total / total_cores / 1024**3 if total_cores != 0 else 0
        opening = f"only used {cpu_memory_utilization}%" if cpu_memory_utilization >= 1 \
                                                         else "used less than 1%"
        if self.js.cluster in c.CORES_PER_NODE:
            cpn = c.CORES_PER_NODE[self.js.cluster]
        else:
            cpn = 0
        if self.js.cluster in c.DEFAULT_MEM_PER_CORE:
            mpc = c.DEFAULT_MEM_PER_CORE[self.js.cluster]
        else:
            mpc = 0
        # loop over notes
        for condition, note, style in c.NOTES:
            if eval(condition):
                if isinstance(note, str):
                    note = (note,)
                note_eval = []
                for item in note:
                    # evaluate f-strings if found
                    if ('f"' in item or "f'" in item) and "{" in item and "}" in item:
                        note_eval.append(eval(item))
                    else:
                        note_eval.append(item)
                s += self.format_note(*note_eval, style=style)
        return s


class ClassicOutput(BaseFormatter):
    """Classic output formatter for the job report."""

    def __init__(self, js: Jobstats):
        super().__init__(js)

    def output(self, no_color: bool=True) -> str:
        if blessed_is_available and not no_color:
            term = Terminal()
            self.txt_bold   = f"{term.bold}"
            self.txt_red    = f"{term.red}"
            self.txt_normal = f"{term.normal}"
        else:
            self.txt_bold   = ""
            self.txt_red    = ""
            self.txt_normal = ""
        ########################################################################
        #                               JOB METADATA                           #
        ########################################################################
        report = "\n"
        report += 80 * "=" + "\n"
        report += "                              Slurm Job Statistics\n"
        report += 80 * "=" + "\n"
        report += f"         Job ID: {self.txt_bold}{self.js.jobid}{self.txt_normal}\n"
        report += f"  NetID/Account: {self.js.user}/{self.js.account}\n"
        report += f"       Job Name: {self.js.jobname}\n"
        if self.js.state in ("OUT_OF_MEMORY", "TIMEOUT"):
            report += f"          State: {self.txt_bold}{self.txt_red}{self.js.state}{self.txt_normal}\n"
        else:
            report += f"          State: {self.js.state}\n"
        report += f"          Nodes: {self.js.nnodes}\n"
        report += f"      CPU Cores: {self.js.ncpus}\n"
        report += self.cpu_memory_formatted() + "\n"
        if self.js.gpus:
            report += f"           GPUs: {self.js.gpus}\n"
        report += f"  QOS/Partition: {self.js.qos}/{self.js.partition}\n"
        report += f"        Cluster: {self.js.cluster}\n"
        report += f"     Start Time: {self.human_datetime(self.js.start)}\n"
        in_progress = " (in progress)" if self.js.state == "RUNNING" else ""
        report += f"       Run Time: {self.human_seconds(self.js.diff)}{in_progress}\n"
        report += self.time_limit_formatted() + "\n"
        report += "\n"
        report += f"                              {self.txt_bold}Overall Utilization{self.txt_normal}\n"
        report += 80 * "=" + "\n"
        ########################################################################
        #                           OVERALL UTILIZATION                        #
        ########################################################################
        # overall cpu time utilization
        total_used, total, total_cores = self.js.cpu_util_total__used_alloc_cores
        self.js.cpu_efficiency = round(100 * total_used / total) if total != 0 else 0
        meter = self.draw_meter(self.js.cpu_efficiency, "cpu", util=True)
        report += "  CPU utilization  " + meter + "\n"
        # overall cpu memory utilization
        total_used, total, total_cores = self.js.cpu_mem_total__used_alloc_cores
        cpu_memory_efficiency = round(100 * total_used / total) if total != 0 else 0
        report += "  CPU memory usage " + self.draw_meter(cpu_memory_efficiency, "cpu") + "\n"
        if self.js.gpus:
            # overall gpu utilization
            overall, overall_gpu_count = self.js.gpu_util_total__util_gpus
            self.js.gpu_utilization = overall / overall_gpu_count
            if self.js.partition == "mig":
                unknown = f"  GPU utilization  {self.txt_bold}[{self.txt_normal}" \
                          f"     GPU utilization is unknown for MIG jobs      " \
                          f"{self.txt_normal}{self.txt_bold}]{self.txt_normal}"
                report += unknown + "\n"
            else:
                meter = self.draw_meter(round(self.js.gpu_utilization), "gpu", util=True)
                report += "  GPU utilization  " + meter + "\n"
            # overall gpu memory usage
            overall, overall_total = self.js.gpu_mem_total__used_alloc
            gpu_memory_usage = round(100 * overall / overall_total)
            report += "  GPU memory usage " + self.draw_meter(gpu_memory_usage, "gpu") + "\n"
        report += "\n"

        ########################################################################
        #                          DETAILED UTILIZATION                        #
        ########################################################################
        report += f"                              {self.txt_bold}Detailed Utilization{self.txt_normal}\n"
        report += 80 * "=" + "\n"
        gutter = "  "
        # cpu time utilization
        report += f"{gutter}CPU utilization per node (CPU time used/run time)\n"
        for node, used, alloc, cores in self.js.cpu_util__node_used_alloc_cores:
            msg = ""
            if used == 0:
                msg = f" {self.txt_bold}{self.txt_red}<-- CPU node was not used{self.txt_normal}"
            hs_used = self.human_seconds(used)
            hs_alloc = self.human_seconds(alloc)
            eff = 100 * used / alloc
            report += f"{gutter}    {node}: {hs_used}/{hs_alloc} (efficiency={eff:.1f}%){msg}\n"
        if self.js.nnodes != "1":
            used, alloc, _ = self.js.cpu_util_total__used_alloc_cores
            hs_used = self.human_seconds(used)
            hs_alloc = self.human_seconds(alloc)
            eff = 100 * used / alloc
            report += f"{gutter}Total used/runtime: {hs_used}/{hs_alloc}, efficiency={eff:.1f}%\n"
        # cpu memory usage
        report += f"\n{gutter}CPU memory usage per node - used/allocated\n"
        for node, used, alloc, cores in self.js.cpu_mem__node_used_alloc_cores:
            hb_alloc = self.human_bytes(alloc).replace(".0GB", "GB")
            report += f"{gutter}    {node}: {self.human_bytes(used)}/{hb_alloc} "
            hb_alloc = self.human_bytes(alloc / cores).replace(".0GB", "GB")
            report += f"({self.human_bytes(used*1.0/cores)}/{hb_alloc} per core of {cores})\n"
        total_used, total, total_cores = self.js.cpu_mem_total__used_alloc_cores
        if self.js.nnodes != "1":
            report += f"{gutter}Total used/allocated: {self.human_bytes(total_used)}/{self.human_bytes(total)} "
            hb_total = self.human_bytes(total / total_cores).replace(".0GB", "GB")
            report += f"({self.human_bytes(total_used*1.0/total_cores)}/{hb_total} per core of {total_cores})\n"
        if self.js.gpus:
            # gpu utilization
            report += f"\n{gutter}GPU utilization per node\n"
            if self.js.partition == "mig":
                report += f"{gutter}    {node} (GPU): GPU utilization is unknown for MIG jobs\n"
            else:
                for node, util, gpu_index in self.js.gpu_util__node_util_index:
                    msg = ""
                    if util == 0:
                        msg = f" {self.txt_bold}{self.txt_red}<-- GPU was not used{self.txt_normal}"
                    report += f"{gutter}    {node} (GPU {gpu_index}): {util}%{msg}\n"
            # gpu memory usage
            report += f"\n{gutter}GPU memory usage per node - maximum used/total\n"
            for node, used, total, gpu_index in self.js.gpu_mem__node_used_total_index:
                hs_used = self.human_bytes(used)
                hs_total = self.human_bytes(total).replace(".0GB", "GB")
                eff = 100 * used / total
                report += f"{gutter}    {node} (GPU {gpu_index}): {hs_used}/{hs_total} ({eff:.1f}%)\n"
        ########################################################################
        #                              JOB NOTES                               #
        ########################################################################
        report += "\n"
        notes = self.job_notes()
        if notes:
            report += f"                                     {self.txt_bold}Notes{self.txt_normal}\n"
            report += 80 * "=" + "\n"
            report += notes
        return report
