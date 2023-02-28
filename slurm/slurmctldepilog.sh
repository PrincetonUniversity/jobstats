#!/bin/bash
# it looks like that this is sometimes too fast, wait a tiny bit to let slurmdbd get the data it needs
sleep 5s
# We need to treat differently array jobs where jobid=slurm array jobid or else we will overwrite all
# array jobs with the same data. Therefore use ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} instead of
# jobid for those jobs.
if [ "x$SLURM_ARRAY_JOB_ID" = "x$SLURM_JOB_ID" ]; then
	INTERNAL_JOBID=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}
else
	INTERNAL_JOBID=$SLURM_JOB_ID
fi
logger SlurmctldEpilog[$INTERNAL_JOBID]: Begin processing
STATS="`jobstats -f -b $SLURM_JOB_ID`"
ERR=$?
if [ $ERR = 0 ]; then
	if [[ $STATS =~ ^(Short|None|H4s) ]]; then
		logger "SlurmctldEpilog[$INTERNAL_JOBID]: Success with output $STATS"
		OUT="`sacctmgr -i update job where jobid=$INTERNAL_JOBID set AdminComment=JS1:$STATS 2>&1`"
		if [ $? != 0 ]; then
			logger "SlurmctldEpilog[$INTERNAL_JOBID]: Errored out when storing AdminComment with $OUT"
		fi
	else
		logger "SlurmctldEpilog[$INTERNAL_JOBID]: Apparent success but invalid output $STATS"
	fi
else
	logger "SlurmctldEpilog[$INTERNAL_JOBID]: Failed to process with error $ERR and output $STATS"
fi
logger SlurmctldEpilog[$INTERNAL_JOBID]: End processing
exit 0
