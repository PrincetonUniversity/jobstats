# External Database Configuration

This section describes how to configure Jobstats to use an external MariaDB/MySQL database instead of storing job summary statistics in the `AdminComment field of the Slurm database.

## Overview

By default, Jobstats stores job statistics in the Slurm database by updating the `AdminComment` field in the job table. The feature described here allows for storing the statistics in a separate external MariaDB/MySQL database instead. This is useful for:

- Separating Jobstats data from the Slurm database
- Easier data analysis and reporting
- Database backup and maintenance flexibility

## Configuration

### 1. Database Setup

First, create a MariaDB/MySQL database and table to store the job statistics:

```sql
CREATE DATABASE jobstats;
USE jobstats;

CREATE TABLE job_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cluster VARCHAR(50) NOT NULL,
    jobid VARCHAR(50) NOT NULL,
    admin_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_cluster_job (cluster, jobid)
);
```

### 2. Python Dependencies

Install the required MySQL client library:

```bash
# For conda environments
conda install mysqlclient

# Or using pip
pip install mysqlclient
```

### 3. Configuration File

Edit `config.py` to enable external database support:

```python
EXTERNAL_DB_CONFIG = {
    "enabled": True,  # Set to True to enable external DB
    "host": "your-database-host",
    "port": 3306,
    "database": "jobstats",
    "user": "jobstats_user",
    "password": "your_password",
    # Alternatively, use a MySQL config file:
    # "config_file": "/path/to/mysql.cnf"
}
```

#### Using MySQL Configuration File (Recommended)

For better security, one can use a MySQL configuration file instead of hardcoding the credentials:

```python
EXTERNAL_DB_CONFIG = {
    "enabled": True,
    "database": "jobstats",
    "config_file": "/etc/jobstats/mysql.cnf"
}
```

Create the MySQL config file (`/etc/jobstats/mysql.cnf`):
```ini
[client]
host = your-database-host
port = 3306
user = jobstats_user
password = your_password
```

### 4. Script Installation

Copy the `store_jobstats.py` script to `/usr/local/bin/` on your Slurm controller:

```bash
sudo cp store_jobstats.py /usr/local/bin/
sudo chmod +x /usr/local/bin/store_jobstats.py
```

### 5. Slurm Configuration

Update your `slurmctldepilog.sh` script. The script will automatically detect the presence of `store_jobstats.py` and use external database storage when available.

## How It Works

### Storage Behavior

- **External DB enabled**: Job statistics are stored only in the external database
- **External DB disabled**: Job statistics are stored in `AdminComment` in Slurm DB (default behavior)

### Epilog Script Logic

The `slurmctldepilog.sh` script uses the following conditional logic:

&nbsp;&nbsp;&nbsp;&nbsp;If `/usr/local/bin/store_jobstats.py` exists:

- store jobstats in external database only
- log success/failure for the attempt

&nbsp;&nbsp;&nbsp;&nbsp;If `/usr/local/bin/store_jobstats.py` does NOT exist:

- use traditional Slurm `AdminComment` storage (maintains backward compatibility)

This ensures that:

- systems without external DB setup continue to work normally  
- systems with external DB use only the external database (no fallback)

### Data Retrieval

When using the `jobstats` command:

- the Slurm `AdminComment` field is checked for compatibility with existing data
- if no data found and external DB is enabled then retrieve from external database

## Migration

From Slurm `AdminComment` to External DB:

1. Set up the external database and configure `config.py`
2. Install the `store_jobstats.py` script
3. Future jobs will automatically use the external database

## Troubleshooting

Common issues:

1. **MySQLdb import error**: Install `mysqlclient` package
2. **Connection failed**: Check database credentials and network connectivity
3. **Permission denied**: Ensure `store_jobstats.py` is executable
4. **Storage handler failed**: Check database permissions and table existence
