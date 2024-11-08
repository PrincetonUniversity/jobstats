# Utilization Reports

This is a tool for sending detailed usage reports to users or group leaders by email.

Users can receive an email utilization report upon completion of each job via Slurm directives. Because some users decide not to receive these emails, it is important to periodically send a comprehensive utilization report to each user. As discussed earlier, summary statistics for each completed job are stored in a compressed format in the `AdminComment` field of the Slurm database. The software described here works by calling `sacct` while requesting several fields including `AdminComment`. The `sacct` output is stored in a `pandas` dataframe for processing.

Each user that ran at least one Slurm job in the specified time interval will receive a report when the software is run. The first part of the report is a table that indicates the overall usage for each cluster. Each row provides the CPU-hours, GPU-hours, number of jobs, and Slurm account(s) and partition(s) that were used by the user.

The second part of the report is a detailed table showing for each partition of each cluster the CPU-hours, CPU-rank, CPU-eff, GPU-hours, GPU-rank, GPU-eff and number of jobs. The CPU-rank or GPU-rank indicates the user's usage relative to the other users on the given partition of the cluster. CPU-eff (or GPU-eff) is the overall CPU (or GPU) efficiency which varies from 0-100%. A responsible user will take action when seeing that their rank is high while their efficiency is low. The email report also provides a definition for each reported quantity. The software could be extended by adding queue hours and data storage information to the tables.

## Usage

The default mode of the software is to send user reports. It can also be used to send reports to those that are responsible for the users such as the principal investigator. This is the so-called `sponsors` mode. The example below shows how the script is called to generate user reports over the past month which are sent by email:

```
$ utilization_reports --report-type=users --months=1 --email
```

## Installation

We find a good choice is to send the report once per month. The installation requirements for the software are Python 3.6+ and version 1.2+ of the `pandas` package. The Python code, example reports, and instructions are available at <a href="https://github. com/PrincetonUniversity/monthly_sponsor_reports" target="_blank">https://github.com/PrincetonUniversity/monthly_sponsor_reports</a>.
