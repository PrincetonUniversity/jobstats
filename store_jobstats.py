#!/usr/bin/env python3
import argparse
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
    
    print("Successfully stored jobstats")

if __name__ == "__main__":
    main()
