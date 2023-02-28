#!/bin/bash
DEST=/run/gpustat
[ -e $DEST ] || mkdir -m 755 $DEST
for i in ${GPU_DEVICE_ORDINAL//,/ } ${CUDA_VISIBLE_DEVICES//,/ }; do
  echo $SLURM_JOB_ID $SLURM_JOB_UID > $DEST/$i
done
exit 0
