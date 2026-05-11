#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
try:
    import MySQLdb
except ImportError:
    MySQLdb = None

# realpath resolve the script's real location when invoked through a symlink
# (e.g. /usr/local/bin/store_jobstats.py -> /usr/local/jobstats/store_jobstats.py).
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from db_handler import JobstatsDBHandler
from config import EXTERNAL_DB_CONFIG


def parse_jobid(value):
    """Parse a raw numeric Slurm job ID for external DB storage."""
    jobid = value.strip()
    if not jobid or not jobid.isdigit():
        raise argparse.ArgumentTypeError(
            f"Job ID must be a raw numeric Slurm job ID, got {value!r}"
        )
    return int(jobid)


def mirror_to_admin_comment(jobid, stats):
    """Mirror the JS1 payload to the Slurm AdminComment field via sacctmgr.

    A failure here does not fail the script: the external database write has
    already succeeded and AdminComment is a secondary, best-effort target
    for sacct-based consumers (e.g. reportseff).
    """
    try:
        result = subprocess.run(
            ["sacctmgr", "-i", "update", "job",
             f"jobid={jobid}", "set", f"AdminComment={stats}"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            print(
                f"WARNING: sacctmgr failed to mirror AdminComment for job "
                f"{jobid} (rc={result.returncode}): "
                f"{(result.stderr or result.stdout).strip()}",
                file=sys.stderr,
            )
    except FileNotFoundError:
        print(
            "WARNING: sacctmgr not found; cannot mirror to AdminComment.",
            file=sys.stderr,
        )
    except Exception as exc:
        print(
            f"WARNING: unexpected error while mirroring AdminComment for "
            f"job {jobid}: {exc}",
            file=sys.stderr,
        )


def main():
    parser = argparse.ArgumentParser(description="Store jobstats to external and/or Slurm database")
    parser.add_argument("--cluster", required=True, help="Cluster name")
    parser.add_argument(
        "--jobid",
        required=True,
        type=parse_jobid,
        help="Raw Slurm job ID",
    )
    parser.add_argument("--stats", required=True, help="Job statistics")
    
    args = parser.parse_args()
    
    db_handler = JobstatsDBHandler()
    
    # Check if external DB is enabled and available
    if not EXTERNAL_DB_CONFIG.get("enabled", False):
        print("ERROR: External database is not enabled in config.py", file=sys.stderr)
        sys.exit(1)
    
    # Check if MySQLdb is available
    if MySQLdb is None:
        print("ERROR: MySQLdb module not available. Install mysqlclient to use external database functionality.", file=sys.stderr)
        sys.exit(1)
    
    # Save to external database
    errors = db_handler.save_jobstats(args.cluster, args.jobid, args.stats, None)
    
    if errors:
        print(f"Errors occurred: {'; '.join(errors)}", file=sys.stderr)
        sys.exit(1)

    # Optionally mirror the payload to AdminComment for sacct-based consumers
    # (e.g. reportseff). Best-effort: failures are logged but do not fail the
    # script because the external DB write has already succeeded.
    if EXTERNAL_DB_CONFIG.get("mirror_to_admin_comment", False):
        mirror_to_admin_comment(args.jobid, args.stats)

    print("Successfully stored jobstats")

if __name__ == "__main__":
    main()
