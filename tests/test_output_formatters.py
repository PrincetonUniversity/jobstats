import time
from jobstats import Jobstats
from output_formatters import ClassicOutput
import pytest


@pytest.fixture
def simple_stats(mocker):
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    ss64 = ('JS1:H4sIADelIWcC/1WNQQqDMBBF7zLrtEzG0ZhcphQzqGBM0bgQyd0bUii4fe8'
            '//gVr9LKDuyDNo2yPibpBr00FMb2XV5AQtxOcRtMY1j0xKjh28X/TdsRMhRfxa9'
            'IcBJyxbPsnKRg+R3lgzPk+ICSrYKwW8xcnjeJ8iwAAAA==')
    data = ('10920562|1730212549|Unknown|tiger2|billing=40,cpu=40,mem=10G,no'
            'de=1|%s|aturing|physics|RUNNING|1|40|10G|tiger-short|serial|144'
            '0|myjob\n' % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="DUMMY-JOBID", prom_server="DUMMY-SERVER")
    return stats


def test_human_bytes(simple_stats):
    formatter = ClassicOutput(simple_stats)
    assert formatter.human_bytes(42) == "42.0B"
    assert formatter.human_bytes(1024**3) == "1.0GB"
    assert formatter.human_bytes(4_000_000_000) == "3.7GB"
    assert formatter.human_bytes(4_000_000_000_000) == "3.6TB"
    assert formatter.human_bytes(4_000_000_000_000_000) == "3.6PB"


def test_human_seconds(simple_stats):
    formatter = ClassicOutput(simple_stats)
    assert formatter.human_seconds(42) == "00:00:42"
    assert formatter.human_seconds(420) == "00:07:00"
    assert formatter.human_seconds(4200) == "01:10:00"
    assert formatter.human_seconds(42003) == "11:40:03"
    assert formatter.human_seconds(420002) == "4-20:40:02"
    assert formatter.human_seconds(4200001) == "48-14:40:01"


def test_human_datetime(simple_stats):
    formatter = ClassicOutput(simple_stats)
    secs_since_epoch = 1730298181
    # shift to Eastern Time Zone (-0400)
    hours = int(time.strftime("%z")) / 100 + 4
    secs_since_epoch += hours * 60 * 60
    expected = "Wed Oct 30, 2024 at 10:23 AM"
    assert formatter.human_datetime(secs_since_epoch) == expected
    secs_since_epoch = 1730298181 - 29 * 24 * 60 * 60 + 12 * 60 * 60
    # shift to EDT (-0400)
    hours = int(time.strftime("%z")) / 100 + 4
    secs_since_epoch += hours * 60 * 60
    expected = "Tue Oct 1, 2024 at 10:23 PM"
    assert formatter.human_datetime(secs_since_epoch) == expected


def test_cpu_memory_formatted(simple_stats):
    formatter = ClassicOutput(simple_stats)
    assert formatter.cpu_memory_formatted(with_label=False) == "10GB"
    expected = "     CPU Memory: 10GB (250MB per CPU-core)"
    assert formatter.cpu_memory_formatted() == expected
    # no prefix (e.g., 10G)
    formatter.js.reqmem = "10"
    assert formatter.cpu_memory_formatted(with_label=False) == "10"
    formatter.js.reqmem = "10000G"
    assert formatter.cpu_memory_formatted(with_label=False) == "10TB"
    formatter.js.reqmem = "100.5G"
    formatter.js.ncpus = 9
    expected = "     CPU Memory: 100.5GB (11.2GB per CPU-core)"
    assert formatter.cpu_memory_formatted() == expected


def test_rounded_memory_with_safety(simple_stats):
    formatter = ClassicOutput(simple_stats)
    assert formatter.rounded_memory_with_safety(0) == 1
    assert formatter.rounded_memory_with_safety(9) == 11
    assert formatter.rounded_memory_with_safety(26) == 35
    assert formatter.rounded_memory_with_safety(90) == 110
    assert formatter.rounded_memory_with_safety(900) == 1100
    assert formatter.rounded_memory_with_safety(2600) == 3200


def test_time_limit_formatted(simple_stats):
    formatter = ClassicOutput(simple_stats)
    assert formatter.time_limit_formatted() == "     Time Limit: 1-00:00:00"
    formatter.js.timelimitraw = 4242
    assert formatter.time_limit_formatted() == "     Time Limit: 2-22:42:00"


def test_draw_meter(simple_stats):
    formatter = ClassicOutput(simple_stats)
    bars = "|" * (75 // 2)
    spaces = " " * (50 - len(bars) - 3)
    assert formatter.draw_meter(75, "cpu") == f"[{bars}{spaces}75%]"
