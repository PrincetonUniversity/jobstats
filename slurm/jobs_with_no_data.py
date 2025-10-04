#!/usr/bin/python3

import argparse
import os
import subprocess
import sys
import MySQLdb
import time

DB='slurm_acct_db'
DEVNULL = open(os.devnull, 'w')

# report an error on stderr and fail
def error(msg):
    sys.stderr.write(f"{msg}\n")
    sys.exit(1)

def warn(msg):
    sys.stderr.write(f"{msg}\n")

def get_current_jobs(cluster):
    cmd = ["/usr/bin/squeue", "--noheader", "-M", cluster, "-o","%A" ]
    return [ i for i in subprocess.check_output(cmd,stderr=DEVNULL).decode("utf-8").split('\n') if i != '' ]

def get_jobs_to_process(conn, cluster, num, days):
    if days == 0:
        time_end = 0
    else:
        time_end = int(time.time() - 24*days*60*60)
    running_jobs = get_current_jobs(cluster)
    cur = conn.cursor()
    cur.execute(f"select id_job,id_array_job,id_array_task from {cluster}_job_table where admin_comment IS NULL and time_start > 0 and time_end > {time_end} ORDER BY id_job DESC LIMIT {num}")
    jobs = []
    for id_job,id_array_job,id_array_task in cur.fetchall():
        if id_job in running_jobs:
            continue
        # An array job looks like id_job=2666514, id_array_job=2666501, id_array_task=9
        # Non array job looke like id_job=2666518, id_array_job=0, id_array_task=4294967294
        if id_array_job != 0:
            if id_array_task == 4294967294:
                warn(f"Ignoring array job {id_job}, array job id {id_array_job} with array task = {id_array_task}")
            else:
                jobs.append(f"{id_array_job}_{id_array_task}")
        else:
            jobs.append(id_job)
    return jobs

def run_processing(cluster, num, days):
    conn = MySQLdb.connect(db=DB,read_default_file='/root/.my.cnf')
    db_jobs = get_jobs_to_process(conn, cluster, num, days)
    for i in db_jobs:
        print(i)

parser = argparse.ArgumentParser(description="Return job ids of jobs that do not have AdminComment set.")
parser.add_argument("-c", "--cluster", required=True,
                    help="cluster for which to check stats.")
parser.add_argument("-n", "--num", type=int, default=1000,
                    help="maximum number of recent jobs with no stats to check/retur/returnn")
parser.add_argument("-d", "--days", type=int, default=365,
                    help="how many days back to look for jobs with no AdminComment. Set to 0 to look throught the db. Default is 365 days.")
args = parser.parse_args()

run_processing(args.cluster, args.num, args.days)
