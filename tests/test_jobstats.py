import base64
import gzip
import json
import pytest
from jobstats import Jobstats


@pytest.fixture
def simple_cpu_job(mocker):
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
def cpu_total_time_missing(mocker):
    """A job where the total_time key is missing in the JSON."""
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    nodes = {"della-r1c4n3": {"cpus": 15, "total_memory": 1073741824}}
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
    """A job where the used_memory key is missing in the JSON."""
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
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
    """A job where total_memory is zero."""
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
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


@pytest.fixture
def simple_gpu_job(mocker):
    """A GPU job without issues."""
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    ss64 = ('JS1:H4sIAKA3KmcC/12OTQ6DIBCF7zJra4AZYPAyxlRiSFBMi4vWcPdqbZvY5cv'
            '73s8KU+r9HZoVeh9jd4lCDhJ3nVPuYjv6Md0e0Ei0hOw0klUVLHff/ywmw2iFUr'
            'tzpHIYPTTaGiVqruA6L9uE3OxhXtpz8Qpyq9DsHJJ2SpQDOi0cDKIkNqwUfZkcY'
            'nh2OaTpwziuTSnl74ZwRO/EfqK8APTfhRDzAAAA')
    data = ('60155093|1730723367|1730774311|della|billing=10485,cpu=12,gres/'
            'gpu=1,mem=128G,node=1|%s|aturing|cs|COMPLETED|1|12|128G|gpu-sho'
            'rt|gpu-shared|990|emb\n' % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="60155093", prom_server="DUMMY-SERVER")
    return stats


@pytest.fixture
def gpu_utilization_missing(mocker):
    """A job where the gpu_utilization key is missing in the JSON."""
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    ss64 = ('JS1:H4sIAOBg0WgC/12MywqAIBAA/2XPFrtaVv5MRC4RaEbZIcJ/70F06DozzAF'
            'TsLyCOcCyc122qL6YSN0ghti51rMPyw5G6QqRNKKAbWX7cS0LWZHS4u3j6BkMNd'
            'iUuRTQz9t1p5T+XtYkYHgsphOwrZPFhwAAAA==')
    data = ('845136|1758532566|1758551847|della|billing=1,cpu=1,mem=350M,nod'
            'e=1,gres/gpu=1|%s|aturing|achurch|COMPLETED|1|1|350M|short|cpu|'
            '1439|onebitdiff_posterior_entropy_nsamples.sh\n' % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="845136", prom_server="DUMMY-SERVER")
    return stats


@pytest.fixture
def gpu_used_memory_missing(mocker):
    """A job where the used_memory key is missing in the JSON."""
    cols = ('JobIDRaw|Start|End|Cluster|AllocTRES|AdminComment|User|Account|'
            'State|NNodes|NCPUS|ReqMem|QOS|Partition|TimelimitRaw|JobName\n')
    js_data = {
                "gpus": 1,
                "nodes": {
                    "della-l04g11": {
                        "cpus": 1,
                        "gpu_total_memory": {
                            "2": 85899345920
                        },
                        "gpu_utilization": {
                            "2": 0
                        },
                        "total_memory": 268435456000,
                        "total_time": 11423.0,
                        "used_memory": 10614919168
                    }
                },
                "total_time": 11540
              }
    data = json.dumps(js_data, sort_keys=True, indent=4)
    ss64 = "JS1:" + base64.b64encode(gzip.compress(data.encode('ascii'))).decode('ascii')
    data = ('46915114|1681342706|1681354246|della|billing=20480,cpu=1,gres/g'
            'pu=1,mem=250G,node=1|%s|aturing|ee|CANCELLED by 223988|1|1|250G'
            '|gpu-short|gpu|840|run_main_1.cmd\n' % ss64)
    sacct_bytes = bytes(cols + data, "utf-8")
    mocker.patch("subprocess.check_output", return_value=sacct_bytes)
    stats = Jobstats(jobid="46915114", prom_server="DUMMY-SERVER")
    return stats


def test_simple_cpu_job(mocker, simple_cpu_job):
    total_cpu_time = simple_cpu_job.diff * int(simple_cpu_job.ncpus)
    expected = (79498.2, total_cpu_time, 40)
    assert simple_cpu_job.cpu_util_total__used_alloc_cores == expected
    assert simple_cpu_job.cpu_util_error_code == 0
    expected = (5624422400, 10737418240, 40)
    assert simple_cpu_job.cpu_mem_total__used_alloc_cores == expected
    assert simple_cpu_job.cpu_mem_error_code == 0
    assert simple_cpu_job.gpus == 0


def test_cpu_total_time_missing(mocker, cpu_total_time_missing):
    assert cpu_total_time_missing.cpu_mem_error_code == 1


def test_cpu_used_memory_missing(mocker, cpu_used_memory_missing):
    assert cpu_used_memory_missing.cpu_mem_error_code == 1


def test_cpu_mem_over_100_percent(mocker, cpu_mem_over_100_percent):
    assert cpu_mem_over_100_percent.cpu_mem_error_code == 2


def test_cpu_total_memory_is_zero(mocker, cpu_total_memory_is_zero):
    assert cpu_total_memory_is_zero.cpu_mem_error_code == 3


def test_simple_gpu_job(mocker, simple_gpu_job):
    assert simple_gpu_job.gpu_util_error_code == 0
    assert simple_gpu_job.gpu_mem_error_code == 0


def test_gpu_utilization_missing(mocker, gpu_utilization_missing):
    assert gpu_utilization_missing.gpu_util_error_code == 1


def test_gpu_used_memory_missing(mocker, gpu_used_memory_missing):
    assert gpu_used_memory_missing.gpu_mem_error_code == 1
