#! /bin/bash

SEFF=/usr/local/bin/jobstats
MAIL=/bin/mail

#### JOB_COMPLETION_TIME ###
# The time needed for job to complete and synchronize accounting data with
# slurmdbd. If you're running slurmctld under systemd control executing
# `systemctl stop slurmctld` or `systemctl restart slurmctld` may hang for this
# time. While slurmctld will be down systemd will still wait for all
# descendant processes (in this case sleep executed from smail) to complete.
# The default value is 5 seconds (half of default MessageTimeout).
JOB_COMPLETION_TIME=5

# Get the ClusterName
ClusterName=${SLURM_CLUSTER_NAME}
subject="$ClusterName $2"
recipient=$3

# as per slurm.conf man page this var is set if job finished
if [ -n "$SLURM_JOB_RUN_TIME" ]; then
    jobid=$SLURM_JOB_ID
    # Fork a child so sleep is asynchronous.
    {
        sleep $JOB_COMPLETION_TIME
	(
	echo "To: $recipient"
	echo "From: slurm@localhost"
	echo "Content-Type: text/html; "
	echo "Subject: $subject"
	echo
	echo "<pre>"
	$SEFF --no-color $jobid
	echo "</pre>" ) | /usr/sbin/sendmail -t
    } &
else
    $MAIL -s "$subject" $recipient
fi
