#!/bin/bash
DEST=/run/gpustat
[ -e $DEST ] || mkdir -m 755 $DEST
for i in ${GPU_DEVICE_ORDINAL//,/ } ${CUDA_VISIBLE_DEVICES//,/ }; do
  rm -f $DEST/$i
  if [ "${i:0:3}" != "MIG" ]; then
    UUID="`/usr/bin/nvidia-smi --query-gpu=uuid --format=noheader,csv -i $i`"
    rm -f "$DEST/$UUID"
  fi
done
exit 0
