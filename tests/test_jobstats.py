import base64
import gzip
import json
from jobstats import Jobstats
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
    stats = Jobstats(jobid="10920562", prom_server="DUMMY-SERVER")
    return stats


@pytest.fixture
def cpu_mem_over_100_percent(mocker):
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    ss64 = ('JS1:H4sIAMnXKGcC/1WNWwqDMBQF93K/05Kbk6jNZoqYiwiJEY0fItl7HxSKn8P'
            'M4Zw05yAb+ZOCxNjfVh7sjA+XXPr4TJLyepBn3aK13BmraN8k/MWjg3XMaNRvUq'
            'Yk5J12AO6saFj29wG7Wq8FGhijaPxqXV+1b7sLiwAAAA==')
    data = ('49589697|1690927903|1690964225|della|billing=15,cpu=15,mem=1G,n'
            'ode=1|%s|aturing|chem|TIMEOUT|1|15|1G|short|cpu|600|scf.cmd\n'
            % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="49589697", prom_server="DUMMY-SERVER")
    return stats


@pytest.fixture
def cpu_used_memory_missing(mocker):
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    # used_memory was removed
    nodes = {"della-r1c4n3": {"cpus": 15, "total_memory": 1073741824, "total_time": 505333.1}}
    js_data = {"gpus": 0, "nodes": nodes, "total_time": 36322}
    data = json.dumps(js_data, sort_keys=True, indent=4)
    ss64 = "JS1:" + base64.b64encode(gzip.compress(data.encode('ascii'))).decode('ascii')
    data = ('49589697|1690927903|1690964225|della|billing=15,cpu=15,mem=1G,n'
            'ode=1|%s|aturing|chem|TIMEOUT|1|15|1G|short|cpu|600|scf.cmd\n'
            % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="49589697", prom_server="DUMMY-SERVER")
    return stats


@pytest.fixture
def cpu_total_memory_is_zero(mocker):
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    # total memory is zero
    nodes = {"della-r1c4n3": {"cpus": 15, "used_memory": 1073741824, "total_memory": 0}}
    js_data = {"gpus": 0, "nodes": nodes, "total_time": 36322}
    data = json.dumps(js_data, sort_keys=True, indent=4)
    ss64 = "JS1:" + base64.b64encode(gzip.compress(data.encode('ascii'))).decode('ascii')
    data = ('49589697|1690927903|1690964225|della|billing=15,cpu=15,mem=1G,n'
            'ode=1|%s|aturing|chem|TIMEOUT|1|15|1G|short|cpu|600|scf.cmd\n'
            % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="49589697", prom_server="DUMMY-SERVER")
    return stats


def test_simple_job(mocker, simple_stats):
    total_cpu_time = simple_stats.diff * int(simple_stats.ncpus)
    expected = (79498.2, total_cpu_time, 40)
    assert simple_stats.cpu_util_total__used_alloc_cores == expected
    assert simple_stats.cpu_util_error_code == 0
    expected = (5624422400, 10737418240, 40)
    assert simple_stats.cpu_mem_total__used_alloc_cores == expected
    assert simple_stats.cpu_mem_error_code == 0
    assert simple_stats.gpus == 0


def test_cpu_used_memory_missing(mocker, cpu_used_memory_missing):
    assert cpu_used_memory_missing.cpu_mem_error_code == 1


def test_cpu_mem_over_100_percent(mocker, cpu_mem_over_100_percent):
    assert cpu_mem_over_100_percent.cpu_mem_error_code == 2


def test_cpu_total_memory_is_zero(mocker, cpu_total_memory_is_zero):
    assert cpu_total_memory_is_zero.cpu_mem_error_code == 3
