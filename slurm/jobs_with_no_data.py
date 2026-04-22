#!/usr/bin/python3

import argparse
import importlib.util
import os
import sys
import time

import MySQLdb

DB = "slurm_acct_db"
DEFAULT_JOBSTATS_DIR = "/usr/local/jobstats"
EXTERNAL_DB_SUMMARY_TABLE = "job_summary"
ARRAY_TASK_ID_SENTINEL = 4294967294


def error(msg):
    sys.stderr.write(f"{msg}\n")
    sys.exit(1)


def warn(msg):
    sys.stderr.write(f"{msg}\n")


def get_time_threshold(days):
    if days == 0:
        return 0
    return int(time.time() - 24 * days * 60 * 60)


def load_jobstats_config():
    jobstats_dir = os.environ.get("JOBSTATS_DIR", DEFAULT_JOBSTATS_DIR)
    config_path = os.path.join(jobstats_dir, "config.py")

    if not os.path.isfile(config_path):
        return {"enabled": False}

    spec = importlib.util.spec_from_file_location("jobstats_runtime_config", config_path)
    if spec is None or spec.loader is None:
        error(f"Failed to load Jobstats config from {config_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "EXTERNAL_DB_CONFIG", {"enabled": False})


def get_external_connection(external_db_config):
    if not external_db_config.get("enabled", False):
        return None

    if external_db_config.get("config_file"):
        return MySQLdb.connect(
            db=external_db_config["database"],
            read_default_file=external_db_config["config_file"],
        )

    return MySQLdb.connect(
        host=external_db_config["host"],
        port=external_db_config["port"],
        user=external_db_config["user"],
        passwd=external_db_config["password"],
        db=external_db_config["database"],
    )


def get_completed_jobs_batch(conn, cluster, time_threshold, limit, offset, missing_admin_comment_only):
    cur = conn.cursor()

    where = ["time_start > 0", "time_end > %s"]
    params = [time_threshold]
    if missing_admin_comment_only:
        where.append("admin_comment IS NULL")

    query = (
        f"SELECT id_job, id_array_job, id_array_task "
        f"FROM {cluster}_job_table "
        f"WHERE {' AND '.join(where)} "
        f"ORDER BY id_job DESC LIMIT %s OFFSET %s"
    )
    params.extend([limit, offset])
    cur.execute(query, params)
    return cur.fetchall()


def format_job_identifier(id_job, id_array_job, id_array_task, use_raw_ids):
    raw_jobid = str(id_job)

    if id_array_job != 0:
        if id_array_task == ARRAY_TASK_ID_SENTINEL:
            warn(
                f"Ignoring array job {id_job}, array job id {id_array_job} "
                f"with array task = {id_array_task}"
            )
            return None
        if use_raw_ids:
            return raw_jobid
        return f"{id_array_job}_{id_array_task}"

    return raw_jobid


def get_existing_external_jobids(conn, cluster, jobids):
    if not jobids:
        return set()

    placeholders = ",".join(["%s"] * len(jobids))
    query = (
        f"SELECT jobid FROM {EXTERNAL_DB_SUMMARY_TABLE} "
        f"WHERE cluster = %s AND jobid IN ({placeholders})"
    )

    cur = conn.cursor()
    cur.execute(query, [cluster, *jobids])
    return {str(row[0]) for row in cur.fetchall()}


def get_jobs_to_process_slurm(conn, cluster, num, days):
    time_threshold = get_time_threshold(days)
    rows = get_completed_jobs_batch(
        conn,
        cluster,
        time_threshold,
        num,
        0,
        missing_admin_comment_only=True,
    )

    jobs = []
    for row in rows:
        jobid = format_job_identifier(*row, use_raw_ids=False)
        if jobid is not None:
            jobs.append(jobid)
    return jobs


def get_jobs_to_process_external(slurm_conn, external_conn, cluster, num, days):
    time_threshold = get_time_threshold(days)
    jobs = []
    offset = 0
    batch_size = max(num, 100)

    while len(jobs) < num:
        rows = get_completed_jobs_batch(
            slurm_conn,
            cluster,
            time_threshold,
            batch_size,
            offset,
            missing_admin_comment_only=False,
        )
        if not rows:
            break

        offset += len(rows)

        raw_jobids = []
        for row in rows:
            jobid = format_job_identifier(*row, use_raw_ids=True)
            if jobid is not None:
                raw_jobids.append(jobid)

        existing_jobids = get_existing_external_jobids(external_conn, cluster, raw_jobids)
        for jobid in raw_jobids:
            if jobid in existing_jobids:
                continue
            jobs.append(jobid)
            if len(jobs) >= num:
                break

        if len(rows) < batch_size:
            break

    return jobs


def run_processing(cluster, num, days):
    slurm_conn = MySQLdb.connect(db=DB, read_default_file="/root/.my.cnf")
    external_db_config = load_jobstats_config()

    if external_db_config.get("enabled", False):
        external_conn = get_external_connection(external_db_config)
        jobs = get_jobs_to_process_external(slurm_conn, external_conn, cluster, num, days)
    else:
        jobs = get_jobs_to_process_slurm(slurm_conn, cluster, num, days)

    for jobid in jobs:
        print(jobid)


parser = argparse.ArgumentParser(
    description="Return job ids of jobs that are missing stored Jobstats data."
)
parser.add_argument(
    "-c",
    "--cluster",
    required=True,
    help="cluster for which to check stats.",
)
parser.add_argument(
    "-n",
    "--num",
    type=int,
    default=1000,
    help="maximum number of recent jobs with missing stats to return",
)
parser.add_argument(
    "-d",
    "--days",
    type=int,
    default=365,
    help=(
        "how many days back to look for jobs with missing stats. "
        "Set to 0 to look through the db. Default is 365 days."
    ),
)
args = parser.parse_args()

run_processing(args.cluster, args.num, args.days)
