#!/bin/bash
DEST=/run/gpustat
[ -e $DEST ] || mkdir -m 755 $DEST
for i in ${GPU_DEVICE_ORDINAL//,/ } ${CUDA_VISIBLE_DEVICES//,/ }; do
  echo $SLURM_JOB_ID $SLURM_JOB_UID > $DEST/$i
  if [ "${i:0:3}" != "MIG" ]; then
    UUID="`/usr/bin/nvidia-smi --query-gpu=uuid --format=noheader,csv -i $i`"
    echo $SLURM_JOB_ID $SLURM_JOB_UID > "$DEST/$UUID"
  fi
done
exit 0
