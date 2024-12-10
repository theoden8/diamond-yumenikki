#!/usr/bin/env bash

set -ex

for video_name in data/video_*/; do
  mp4_name="${video_name%/}.mp4"
  if test -e "$mp4_name"; then
    continue
  fi
  if test $(find "$video_name" -type f -name "*.jpg" | wc -l) -gt 3; then
    ffmpeg -framerate 24 -pattern_type glob -i "${video_name%/}/image_*.jpg" -c:v libx264 -r 24 -pix_fmt bgr24 -y "$mp4_name" \
      -nostdin
  fi
done
