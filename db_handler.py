try:
    import MySQLdb
except ImportError:
    MySQLdb = None
import sys
import json
import base64
import gzip
from config import EXTERNAL_DB_CONFIG

# table names for structured external database schema
EXTERNAL_DB_SUMMARY_TABLE = "job_summary"
EXTERNAL_DB_NODES_TABLE = "job_nodes"
EXTERNAL_DB_GPU_TABLE = "job_gpu_metrics"

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
            FROM {EXTERNAL_DB_SUMMARY_TABLE}
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
    
    def _decode_js1_payload(self, stats):
        """
        Decode JS1: prefixed payload into JSON structure.
        Returns None if stats is not decodable (e.g., 'JS1:Short', 'JS1:None').
        """
        if not stats or not isinstance(stats, str):
            return None
        
        # Handle special cases
        if stats in ('JS1:Short', 'JS1:None'):
            return None
        
        # Must start with JS1:
        if not stats.startswith('JS1:'):
            return None
        
        try:
            # Strip JS1: prefix and decode
            payload = stats[4:]
            decompressed = gzip.decompress(base64.b64decode(payload))
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            print(f"WARNING: Failed to decode JS1 payload: {e}", file=sys.stderr)
            return None
    
    def _save_to_external_db(self, cluster, jobid, stats):
        """Save to external MariaDB database with structured tables"""
        conn = self.get_external_connection()
        
        try:
            # Start transaction
            cur = conn.cursor()
            
            # Decode the payload
            decoded = self._decode_js1_payload(stats)
            
            # Extract root-level fields
            total_time = None
            gpus = None
            if decoded:
                total_time = decoded.get('total_time')
                gpus = decoded.get('gpus')
            
            # Insert/update job_summary
            summary_query = f"""
            INSERT INTO {EXTERNAL_DB_SUMMARY_TABLE} 
            (cluster, jobid, admin_comment, total_time, gpus, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE 
            admin_comment = VALUES(admin_comment),
            total_time = VALUES(total_time),
            gpus = VALUES(gpus),
            updated_at = NOW()
            """
            cur.execute(summary_query, (cluster, jobid, stats, total_time, gpus))
            
            # Get the job_summary_id
            summary_id = cur.lastrowid
            if summary_id == 0:
                # Row was updated, not inserted; fetch the ID
                cur.execute(f"SELECT id FROM {EXTERNAL_DB_SUMMARY_TABLE} WHERE cluster = %s AND jobid = %s", (cluster, jobid))
                result = cur.fetchone()
                if result:
                    summary_id = result[0]
            
            # insert node and GPU metrics
            if decoded and 'nodes' in decoded:
                # Delete existing node/GPU data for this job (cascade will handle GPU metrics)
                cur.execute(f"DELETE FROM {EXTERNAL_DB_NODES_TABLE} WHERE job_summary_id = %s", (summary_id,))
                
                nodes = decoded['nodes']
                
                # Collect all node data for batch insert
                node_rows = []
                node_gpu_data = {}  # Map node_name -> gpu data for later
                
                for node_name, node_data in nodes.items():
                    cpus = node_data.get('cpus')
                    total_memory = node_data.get('total_memory')
                    used_memory = node_data.get('used_memory')
                    node_total_time = node_data.get('total_time')
                    
                    node_rows.append((summary_id, node_name, cpus, total_memory, used_memory, node_total_time))
                    
                    # Store GPU data for this node
                    if 'gpu_utilization' in node_data or 'gpu_used_memory' in node_data or 'gpu_total_memory' in node_data:
                        node_gpu_data[node_name] = {
                            'utilization': node_data.get('gpu_utilization', {}),
                            'used': node_data.get('gpu_used_memory', {}),
                            'total': node_data.get('gpu_total_memory', {})
                        }
                
                # Batch insert all nodes
                if node_rows:
                    node_query = f"""
                    INSERT INTO {EXTERNAL_DB_NODES_TABLE}
                    (job_summary_id, node_name, cpus, total_memory, used_memory, total_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cur.executemany(node_query, node_rows)
                    
                    # Fetch node IDs back
                    cur.execute(f"SELECT id, node_name FROM {EXTERNAL_DB_NODES_TABLE} WHERE job_summary_id = %s", (summary_id,))
                    node_id_map = {row[1]: row[0] for row in cur.fetchall()}
                    
                    # Collect all GPU data for batch insert
                    gpu_rows = []
                    for node_name, gpu_data in node_gpu_data.items():
                        node_id = node_id_map.get(node_name)
                        if not node_id:
                            continue
                        
                        gpu_util = gpu_data['utilization']
                        gpu_used = gpu_data['used']
                        gpu_total = gpu_data['total']
                        
                        # Get all GPU indexes
                        gpu_indexes = set(gpu_util.keys()) | set(gpu_used.keys()) | set(gpu_total.keys())
                        
                        for gpu_idx in gpu_indexes:
                            utilization = gpu_util.get(gpu_idx)
                            used_mem = gpu_used.get(gpu_idx)
                            total_mem = gpu_total.get(gpu_idx)
                            
                            gpu_rows.append((node_id, gpu_idx, utilization, used_mem, total_mem))
                    
                    # Batch insert all GPU metrics
                    if gpu_rows:
                        gpu_query = f"""
                        INSERT INTO {EXTERNAL_DB_GPU_TABLE}
                        (job_node_id, gpu_index, gpu_utilization, gpu_used_memory, gpu_total_memory)
                        VALUES (%s, %s, %s, %s, %s)
                        """
                        cur.executemany(gpu_query, gpu_rows)
            
            # Commit transaction
            conn.commit()
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise Exception(f"Failed to save jobstats to external database: {e}")
    
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
