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
    stats = Jobstats(jobid="DUMMY-JOBID", prom_server="DUMMY-SERVER")
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
