#!/bin/bash

../chromedriver &

export GFORGE_USERNAME=fhir_bot
export GFORGE_PASSWORD=F123123t

python ../drive-gforge.py --generate-select-options
kill %1
exit 0
