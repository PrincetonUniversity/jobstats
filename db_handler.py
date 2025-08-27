try:
    import MySQLdb
except ImportError:
    MySQLdb = None
import sys
from config import EXTERNAL_DB_CONFIG, EXTERNAL_DB_TABLE

class JobstatsDBHandler:
    def __init__(self):
        self.external_db_enabled = EXTERNAL_DB_CONFIG.get("enabled", False)
        self.external_conn = None
        
    def get_external_connection(self):
        """Get connection to external MariaDB database"""
        if MySQLdb is None:
            raise Exception("MySQLdb module not available. Install mysqlclient to use external database functionality.")
            
        if not self.external_conn:
            try:
                if EXTERNAL_DB_CONFIG.get("config_file"):
                    self.external_conn = MySQLdb.connect(
                        db=EXTERNAL_DB_CONFIG["database"],
                        read_default_file=EXTERNAL_DB_CONFIG["config_file"]
                    )
                else:
                    self.external_conn = MySQLdb.connect(
                        host=EXTERNAL_DB_CONFIG["host"],
                        port=EXTERNAL_DB_CONFIG["port"],
                        user=EXTERNAL_DB_CONFIG["user"],
                        passwd=EXTERNAL_DB_CONFIG["password"],
                        db=EXTERNAL_DB_CONFIG["database"]
                    )
            except Exception as e:
                print(f"ERROR: Could not connect to external database: {e}", file=sys.stderr)
                raise
        return self.external_conn
    
    def get_jobstats(self, cluster, jobid):
        """Retrieve jobstats from external database"""
        if not self.external_db_enabled:
            return None
            
        try:
            conn = self.get_external_connection()
            cur = conn.cursor()
            
            query = f"""
            SELECT admin_comment 
            FROM {EXTERNAL_DB_TABLE}
            WHERE cluster = %s AND jobid = %s
            ORDER BY updated_at DESC
            LIMIT 1
            """
            
            cur.execute(query, (cluster, jobid))
            result = cur.fetchone()
            
            if result:
                return result[0]  # Return the admin_comment field
            return None
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve jobstats from external database: {e}", file=sys.stderr)
            return None
    
    def save_jobstats(self, cluster, jobid, stats, slurm_conn=None):
        """Save jobstats to external DB and/or Slurm DB based on configuration"""
        errors = []
        
        # If external DB is enabled, only write there
        if self.external_db_enabled:
            try:
                self._save_to_external_db(cluster, jobid, stats)
            except Exception as e:
                errors.append(f"External DB error: {e}")
        # Otherwise, save to Slurm database
        elif slurm_conn:
            try:
                self._save_to_slurm_db(slurm_conn, cluster, jobid, stats)
            except Exception as e:
                errors.append(f"Slurm DB error: {e}")
        else:
            errors.append("No database connection available")
        
        return errors
    
    def _save_to_external_db(self, cluster, jobid, stats):
        """Save to external MariaDB database"""
        conn = self.get_external_connection()
        cur = conn.cursor()
        
        query = f"""
        INSERT INTO {EXTERNAL_DB_TABLE} 
        (cluster, jobid, admin_comment, created_at, updated_at) 
        VALUES (%s, %s, %s, NOW(), NOW())
        ON DUPLICATE KEY UPDATE 
        admin_comment = VALUES(admin_comment),
        updated_at = NOW()
        """
        
        cur.execute(query, (cluster, jobid, stats))
        conn.commit()
    
    def _save_to_slurm_db(self, conn, cluster, jobid, stats):
        """Save to Slurm database (existing behavior)"""
        if not conn:
            raise Exception("No Slurm database connection provided")
            
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {cluster}_job_table SET admin_comment = %s WHERE id_job = %s",
            (stats, jobid)
        )
        conn.commit()
        
        if cur.rowcount != 1:
            raise Exception(f"Updated {cur.rowcount} rows instead of 1 for job {jobid}")
