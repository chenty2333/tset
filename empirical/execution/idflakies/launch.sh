#!/bin/bash
# runs all 20 detector runs of both modules, 4 at a time
cd "$(dirname "$0")"
for s in aismessages http-request; do for i in $(seq 1 20); do echo "$s $i"; done; done |
  xargs -P 4 -L 1 sh -c 'python3 run_detector.py $0 $1' >> ${HOME}/icst-idflakies/launch.log 2>&1
