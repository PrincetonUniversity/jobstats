# Procedure for Modifying User Email Reports

The `jobstats` command should be configured to replace `smail`, which is the Slurm executable used for sending email reports. To make this change, edit `slurm.conf` as follows:

```
MailProg=/usr/local/bin/jobstats_mail.sh
```

The `jobstats_mail.sh` script is available in the `slurm` directory of the <a href="https://github.com/PrincetonUniversity/jobstats/tree/main/slurm" target="_blank">Jobstats GitHub repository</a>. This script sets the `content-type` to `text/html` so that the email is sent using a fixed-width font.

As always, to receive an email report, users must include the appropriate Slurm directive in their scripts:

```
#SBATCH --mail-type=end
```

!!! note
    When the run time of the job is less than the sampling period of the Prometheus exporters (which is typically 30 seconds), `jobstats` will call `seff` to generate the job report.

