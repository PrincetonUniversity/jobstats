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

    @abstractmethod
    def output_metadata(self) -> str:
        pass

    @abstractmethod
    def output_overall_cpu_util(self) -> str:
        pass

    @abstractmethod
    def output_overall_cpu_memory_usage(self) -> str:
        pass

    @abstractmethod
    def output_overall_gpu_util(self) -> str:
        pass

    @abstractmethod
    def output_overall_gpu_memory_usage(self) -> str:
        pass

    @staticmethod
    def human_bytes(size: int, decimal_places=1) -> str:
        size = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if size < 1024:
                break
            size /= 1024
        return f"{size:.{decimal_places}f}{unit}"

    @staticmethod
    def human_seconds(seconds: int) -> str:
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
    def human_datetime(seconds_since_epoch: int) -> str:
       fmt = "%a %b %-d, %Y at %-I:%M %p"
       return datetime.datetime.fromtimestamp(seconds_since_epoch).strftime(fmt)

    def cpu_memory_formatted(self, with_label=True) -> str:
        """Return the total CPU memory with formatting."""
        total = self.js.reqmem
        if total.endswith("K"):
            bytes_ = float(total.replace("K", "")) * 1e3
        elif total.endswith("M"):
            bytes_ = float(total.replace("M", "")) * 1e6
        elif total.endswith("G"):
            bytes_ = float(total.replace("G", "")) * 1e9
        elif total.endswith("T"):
            bytes_ = float(total.replace("T", "")) * 1e12
        else:
            if with_label:
                return f'     CPU Memory: {total}'
            else:
                return total
        per_core = bytes_ / int(self.js.ncpus)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if per_core < 1000:
                break
            per_core /= 1000
        pc = f"{per_core:.1f}"
        pc = pc.replace(".0", "")
        total = total.replace("000K", "M")
        total = total.replace("000M", "G")
        total = total.replace("000G", "T")
        total = total.replace(".50G", ".5G")
        total = total.replace(".50T", ".5T")
        total = f"{total}B"
        if with_label:
            return f'     CPU Memory: {total} ({pc}{unit} per CPU-core)'
        else:
            return total
 
    @staticmethod
    def rounded_memory_with_safety(mem_used: float) -> int:
        """Return the suggested memory including 20% safety. The input
           value (mem_used) has units of GB."""
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

    def time_limit_formatted(self) -> str:
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

    def draw_meter(self, efficiency:int, hardware:str, util: bool=False) -> str:
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
        """Process the notes in config.py."""
        s = ""
        # compute several quantities which can later be referenced in notes
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
        # interactive job
        cond1 = bool("sys/dashboard/sys/" in self.js.jobname)
        cond2 = bool(self.js.jobname == "interactive")
        interactive_job = bool(cond1 or cond2)
        # low cpu utilization
        somewhat = " " if self.js.cpu_efficiency < c.CPU_UTIL_RED else " somewhat "
        ceff = self.js.cpu_efficiency if self.js.cpu_efficiency > 0 else "less than 1"
        # next three lines needed for serial code using multiple CPU-cores note
        eff_if_serial = 100 / int(self.js.ncpus) if self.js.ncpus != "0" else -1
        serial_ratio = self.js.cpu_efficiency / eff_if_serial
        approx = " approximately " if self.js.cpu_efficiency != round(eff_if_serial) else " "
        # next four lines needed for excess CPU memory note
        gb_per_core = total / total_cores / 1024**3 if total_cores != 0 else 0
        if self.js.cpu_memory_efficiency >= 1:
            opening = f"only used {self.js.cpu_memory_efficiency}%"
        else:
            opening = "used less than 1%"
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

    def __init__(self, js: Jobstats, width: int=80) -> None:
        super().__init__(js)
        self.txt_bold   = ""
        self.txt_red    = ""
        self.txt_normal = ""
        self.width = width

    def output_metadata(self) -> str:
        """Return the job metadata."""
        meta = f"         Job ID: {self.txt_bold}{self.js.jobid}{self.txt_normal}\n"
        meta += f"  NetID/Account: {self.js.user}/{self.js.account}\n"
        meta += f"       Job Name: {self.js.jobname}\n"
        if self.js.state in ("OUT_OF_MEMORY", "TIMEOUT"):
            meta += f"          State: {self.txt_bold}{self.txt_red}{self.js.state}{self.txt_normal}\n"
        else:
            meta += f"          State: {self.js.state}\n"
        meta += f"          Nodes: {self.js.nnodes}\n"
        meta += f"      CPU Cores: {self.js.ncpus}\n"
        meta += self.cpu_memory_formatted() + "\n"
        if self.js.gpus:
            meta += f"           GPUs: {self.js.gpus}\n"
        meta += f"  QOS/Partition: {self.js.qos}/{self.js.partition}\n"
        meta += f"        Cluster: {self.js.cluster}\n"
        meta += f"     Start Time: {self.human_datetime(self.js.start)}\n"
        in_progress = " (in progress)" if self.js.state == "RUNNING" else ""
        meta += f"       Run Time: {self.human_seconds(self.js.diff)}{in_progress}\n"
        meta += self.time_limit_formatted() + "\n"
        return meta

    def output_overall_cpu_util(self) -> str:
        """Return the overall CPU utilization."""
        if self.js.cpu_util_error_code == 0:
            total_used, total, _ = self.js.cpu_util_total__used_alloc_cores
            self.js.cpu_efficiency = round(100 * total_used / total)
            meter = self.draw_meter(self.js.cpu_efficiency, "cpu", util=True)
            cpu_util = f"  CPU utilization  {meter}\n"
        elif self.js.cpu_util_error_code == 1:
            cpu_util = "  CPU utilization  (JSON is malformed)\n"
        elif self.js.cpu_util_error_code == 2:
            cpu_util = "  CPU utilization  (Value was erroneously found to be >100%)\n"
        elif self.js.cpu_util_error_code == 3:
            cpu_util = "  CPU utilization  (Total CPU time was found to be zero)\n"
        else:
            cpu_util = "  CPU utilization  (Something went wrong)\n"
        return cpu_util

    def output_overall_cpu_memory_usage(self) -> str:
        """Return the overall CPU memory usage."""
        if self.js.cpu_mem_error_code == 0:
            total_used, total, _ = self.js.cpu_mem_total__used_alloc_cores
            self.js.cpu_memory_efficiency = round(100 * total_used / total)
            meter = self.draw_meter(self.js.cpu_memory_efficiency, "cpu")
            cpu_mem = f"  CPU memory usage {meter}\n"
        elif self.js.cpu_mem_error_code == 1:
            cpu_mem = "  CPU memory usage (JSON is malformed)\n"
        elif self.js.cpu_mem_error_code == 2:
            cpu_mem = "  CPU memory usage (Value was erroneously found to be >100%)\n"
        elif self.js.cpu_mem_error_code == 3:
            cpu_mem = "  CPU memory usage (Allocated memory was found to be zero)\n"
        else:
            cpu_mem = "  CPU memory usage (Something went wrong)\n"
        return cpu_mem

    def output_overall_gpu_util(self) -> str:
        """Return the overall GPU utilization."""
        if self.js.gpu_util_error_code == 0:
            overall, overall_gpu_count = self.js.gpu_util_total__util_gpus
            self.js.gpu_utilization = overall / overall_gpu_count
            meter = self.draw_meter(round(self.js.gpu_utilization), "gpu", util=True)
            gpu_util = f"  GPU utilization  {meter}\n"
        elif self.js.gpu_util_error_code == 1:
            gpu_util = "  GPU utilization  (Value is unknown)\n"
        else:
            gpu_util = "  GPU utilization  (Something went wrong)\n"
        return gpu_util 

    def output_overall_gpu_memory_usage(self) -> str:
        """Return the overall GPU memory usage."""
        if self.js.gpu_mem_error_code == 0:
            overall, overall_total = self.js.gpu_mem_total__used_alloc
            gpu_memory_usage = round(100 * overall / overall_total)
            meter = self.draw_meter(gpu_memory_usage, "gpu")
            gpu_mem = f"  GPU memory usage {meter}\n"
        elif self.js.gpu_mem_error_code == 1:
            gpu_mem = "  GPU memory usage (JSON is malformed)\n"
        elif self.js.gpu_mem_error_code == 2:
            gpu_mem = "  GPU memory usage (Value was erroneously found to be >100%)\n"
        elif self.js.gpu_mem_error_code == 3:
            gpu_mem = "  GPU memory usage (Allocated memory was found to be zero)\n"
        else:
            gpu_mem = "  GPU memory usage (Something went wrong)\n"
        return gpu_mem

    def output(self, no_color: bool=True) -> str:
        if blessed_is_available and not no_color:
            term = Terminal()
            self.txt_bold   = f"{term.bold}"
            self.txt_red    = f"{term.red}"
            self.txt_normal = f"{term.normal}"
        ########################################################################
        #                               JOB METADATA                           #
        ########################################################################
        report = "\n"
        report += self.width * "=" + "\n"
        report += "Slurm Job Statistics".center(self.width) + "\n"
        report += self.width * "=" + "\n"
        report += self.output_metadata()
        report += "\n"
        ########################################################################
        #                           OVERALL UTILIZATION                        #
        ########################################################################
        heading = f"{self.txt_bold}Overall Utilization{self.txt_normal}"
        report += heading.center(self.width) + "\n"
        report += self.width * "=" + "\n"
        # overall CPU time utilization
        report += self.output_overall_cpu_util()
        # overall CPU memory utilization
        report += self.output_overall_cpu_memory_usage()
        # GPUs
        if self.js.gpus:
            # overall GPU utilization
            report += self.output_overall_gpu_util()
            # overall GPU memory usage
            report += self.output_overall_gpu_memory_usage()
        report += "\n"
        ########################################################################
        #                          DETAILED UTILIZATION                        #
        ########################################################################
        heading = f"{self.txt_bold}Detailed Utilization{self.txt_normal}"
        report += heading.center(self.width) + "\n"
        report += self.width * "=" + "\n"
        gutter = "  "
        # CPU time utilization
        report += f"{gutter}CPU utilization per node (CPU time used/run time)\n"
        if self.js.cpu_util_error_code == 0:
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
        else:
            report += f"{gutter}    An error was encountered ({self.js.cpu_util_error_code})\n"
        # CPU memory usage
        report += f"\n{gutter}CPU memory usage per node - used/allocated\n"
        for node, used, alloc, cores in self.js.cpu_mem__node_used_alloc_cores:
            hb_alloc = self.human_bytes(alloc).replace(".0GB", "GB")
            report += f"{gutter}    {node}: {self.human_bytes(used)}/{hb_alloc} "
            hb_alloc = self.human_bytes(alloc / cores).replace(".0GB", "GB")
            report += f"({self.human_bytes(used/cores)}/{hb_alloc} per core of {cores})\n"
        total_used, total, total_cores = self.js.cpu_mem_total__used_alloc_cores
        if self.js.nnodes != "1":
            report += f"{gutter}Total used/allocated: {self.human_bytes(total_used)}/{self.human_bytes(total)} "
            hb_total = self.human_bytes(total / total_cores).replace(".0GB", "GB")
            report += f"({self.human_bytes(total_used/total_cores)}/{hb_total} per core of {total_cores})\n"
        # GPUs
        if self.js.gpus:
            # GPU utilization
            report += f"\n{gutter}GPU utilization per node\n"
            if self.js.gpu_util_error_code == 0:
                for node, util, gpu_index in self.js.gpu_util__node_util_index:
                    msg = ""
                    if util == 0:
                        msg = f" {self.txt_bold}{self.txt_red}<-- GPU was not used{self.txt_normal}"
                    report += f"{gutter}    {node} (GPU {gpu_index}): {util}%{msg}\n"
            else:
                 report += f"{gutter}    An error was encountered ({self.js.gpu_util_error_code})\n"
            # GPU memory usage
            report += f"\n{gutter}GPU memory usage per node - maximum used/total\n"
            if self.js.gpu_mem_error_code == 0:
                for node, used, total, gpu_index in self.js.gpu_mem__node_used_total_index:
                    hs_used = self.human_bytes(used)
                    hs_total = self.human_bytes(total).replace(".0GB", "GB")
                    eff = 100 * used / total
                    report += f"{gutter}    {node} (GPU {gpu_index}): {hs_used}/{hs_total} ({eff:.1f}%)\n"
            else:
                report += f"{gutter}    An error was encountered ({self.js.gpu_mem_error_code})\n"
        ########################################################################
        #                              JOB NOTES                               #
        ########################################################################
        gpu_errors = False
        if self.js.gpus:
            gpu_errors = bool(self.js.gpu_util_error_code > 0 or self.js.gpu_mem_error_code > 0)
        heading = f"{self.txt_bold}Notes{self.txt_normal}"
        if self.js.cpu_util_error_code == 0 and self.js.cpu_mem_error_code == 0 and not gpu_errors:
            report += "\n"
            notes = self.job_notes()
            if notes:
                report += heading.center(self.width) + "\n"
                report += self.width * "=" + "\n"
                report += notes
            return report
        else:
            report += "\n"
            report += heading.center(self.width) + "\n"
            report += self.width * "=" + "\n"
            if self.js.cpu_util_error_code:
                report += f"{gutter}* The CPU utilization could not be determined.\n"
            if self.js.cpu_mem_error_code:
                report += f"{gutter}* The CPU memory usage could not be determined. Try the grafana dashboard.\n"
            if self.js.gpus:
                if self.js.gpu_util_error_code:
                    report += f"{gutter}* The GPU utilization could not be determined.\n"
                if self.js.gpu_mem_error_code:
                    report += f"{gutter}* The GPU memory usage could not be determined.\n"
            report += f"{gutter}* No other notes will be shown.\n"
            report += "\n"
            return report
