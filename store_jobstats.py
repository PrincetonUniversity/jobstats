#!/usr/bin/env python3
import argparse
import sys
import os
import MySQLdb

# Add the parent directory to Python path to import jobstats modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_handler import JobstatsDBHandler
from config import EXTERNAL_DB_CONFIG

def main():
    parser = argparse.ArgumentParser(description="Store jobstats to external and/or Slurm database")
    parser.add_argument("--cluster", required=True, help="Cluster name")
    parser.add_argument("--jobid", required=True, help="Job ID")
    parser.add_argument("--stats", required=True, help="Job statistics")
    
    args = parser.parse_args()
    
    db_handler = JobstatsDBHandler()
    
    # Only use external DB when enabled
    if not EXTERNAL_DB_CONFIG.get("enabled", False):
        print("ERROR: External database is not enabled. This script requires external DB configuration.", file=sys.stderr)
        sys.exit(1)
    
    # Save to external database
    errors = db_handler.save_jobstats(args.cluster, args.jobid, args.stats, None)
    
    if errors:
        print(f"Errors occurred: {'; '.join(errors)}", file=sys.stderr)
        sys.exit(1)
    
    print("Successfully stored jobstats")

if __name__ == "__main__":
    main()
