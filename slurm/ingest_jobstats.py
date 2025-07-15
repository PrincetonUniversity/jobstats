#!/usr/bin/python3

import argparse
import os
import subprocess
import sys
import MySQLdb

# Add the parent directory to Python path to import jobstats modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobstats import Jobstats
from db_handler import JobstatsDBHandler
import config as c

DB='slurm_acct_db'
DEVNULL = open(os.devnull, 'w')

# report an error on stderr and fail
def error(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)

# return gpu tres number
def get_gpu_tres(conn):
    cur = conn.cursor()
    cur.execute("select id from tres_table where name='gpu'")
    gpuid = cur.fetchone()[0]
    if isinstance(gpuid, int):
        return gpuid
    else:
        error("Failed to get GPU id number.")

def get_jobs_to_process(conn, cluster, num):
    # tres_req will contain something like 1=8,2=65536,4=1,5=24,1001=2 so store ,1001= as string to search for
    gpuid = ",%d=" % get_gpu_tres(conn)
    cur = conn.cursor()
    
    # If external DB is enabled, check if jobstats exist
    if c.EXTERNAL_DB_CONFIG.get("enabled", False):
        # Get jobs without jobstats
        db_handler = JobstatsDBHandler()
        try:
            ext_conn = db_handler.get_external_connection()
            ext_cur = ext_conn.cursor()
            
            # Get job IDs that already exist in external DB
            ext_cur.execute(f'SELECT DISTINCT jobid FROM {c.EXTERNAL_DB_TABLE} WHERE cluster = %s', (cluster,))
            existing_external_jobs = set(str(row[0]) for row in ext_cur.fetchall())
            
            # Get all recent jobs from Slurm DB
            cur.execute('select id_job,time_start,time_end,state,tres_req,admin_comment from %s_job_table where time_start > 0 and time_end > 0 ORDER BY id_job DESC LIMIT %d' % (cluster, num))
            jobs = {}
            for id_job,start,end,state,tres,admin_comment in cur.fetchall():
                # Skip if job already has stats in either Slurm admin_comment or external DB
                if admin_comment is not None or str(id_job) in existing_external_jobs:
                    continue
                    
                if gpuid in tres and (gpuid+"0") not in tres:
                    gpus = True
                else:
                    gpus = False
                jobs[id_job] = { "start": start, "end": end, "state": state, "tres": tres, "gpus": gpus }
            
            ext_conn.close()
            
        except Exception as e:
            print(f"ERROR: Failed to check external database: {e}")
            sys.exit(1)  # Fail instead of falling back to Slurm DB
    else:
        # only check Slurm DB
        cur.execute('select id_job,time_start,time_end,state,tres_req from %s_job_table where admin_comment IS NULL and time_start > 0 and time_end > 0 ORDER BY id_job DESC LIMIT %d' % (cluster, num))
        jobs = {}
        for id_job,start,end,state,tres in cur.fetchall():
            if gpuid in tres and (gpuid+"0") not in tres:
                gpus = True
            else:
                gpus = False
            jobs[id_job] = { "start": start, "end": end, "state": state, "tres": tres, "gpus": gpus }
    
    return jobs

def save_jobstats(conn, cluster, jobid, stats):
    db_handler = JobstatsDBHandler()
    
    # If external DB is enabled, only write there
    if c.EXTERNAL_DB_CONFIG.get("enabled", False):
        print("writing to external db")
        errors = db_handler.save_jobstats(cluster, jobid, stats, None)  # Don't pass slurm_conn
    else:
        print("writing to slurm db")
        errors = db_handler.save_jobstats(cluster, jobid, stats, conn)
    
    if errors:
        print(f"ERROR: Failed to save jobstats for job {jobid}: {'; '.join(errors)}")

def get_current_jobs(cluster):
    cmd = ["/usr/bin/squeue", "--noheader", "-M", cluster, "-o","%A" ]
    return [ int(i) for i in subprocess.check_output(cmd,stderr=DEVNULL).decode("utf-8").split('\n') if i != '' ]

def process_job(conn, cluster, jobid, details):
    print("Processing jobid %s on cluster %s" % (jobid, cluster))
    try:
        diff = details['end'] - details['start']
        if diff > 59:
            stats = Jobstats(jobid=jobid, jobidraw=jobid, start=details['start'], end=details['end'], gpus=details['gpus'], cluster=cluster)
            save_stats = "JS1:%s" % stats.report_job_json(encode=True)
        else:
            save_stats = "JS1:Short"
        #print(jobid,stats.diff,save_stats)
        save_jobstats(conn, cluster, jobid, save_stats)
    except Exception as e:
        print("ERROR: Failed to process jobid %s, got error: %s" %(jobid, e))

def run_processing(cluster, num):
    conn = MySQLdb.connect(db=DB,read_default_file='/root/.my.cnf')
    db_jobs = get_jobs_to_process(conn, cluster, num)
    cur_jobs = get_current_jobs(cluster)
    for i in db_jobs:
        state = db_jobs[i]["state"]
        if i in cur_jobs or db_jobs[i]["end"] == 0:
            print("Skipping processing of %s, in current jobs, has state %s, gpus=%s, tres=%s" %(i, state, db_jobs[i]["gpus"], db_jobs[i]["tres"]))
        elif state < 3:
            print("Skipping processing of %s, has state %s" %(i, state))
        else:
            process_job(conn, cluster, i, db_jobs[i])

parser = argparse.ArgumentParser(description="Populate slurm database with summary jobstats for recent jobs without any stats.")
parser.add_argument("-c", "--cluster", required=True,
                    help="cluster for which to check stats.")
parser.add_argument("-n", "--num", type=int, default=1000,
                    help="maximum number of recent jobs with no stats to check")
args = parser.parse_args()

run_processing(args.cluster, args.num)
