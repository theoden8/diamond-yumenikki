#!/usr/bin/env bash

set -ex

if ! test -e "./YN/YN.tar.gz"; then
  mkdir -p ./YN/
  for hdf5_file in ./yume-nikki-data/video_0041/framebatch_{1..79}.hdf5; do
    if ! test -e "./YN/$(basename "$hdf5_file")"; then
      cp -v "$hdf5_file" ./YN/
    fi
  done
  tar czf "./YN/YN.tar.gz" ./YN/*.hdf5
  rm -vf ./YN/*.hdf5
fi

(cd ./AI-MarioKart64/diamond && python ./src/process_dataset_hdf5.py ../../YN ./yn-processed
