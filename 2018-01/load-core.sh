#!/bin/bash

../chromedriver &
#export GFORGE_USERNAME=fhir_bot
#export GFORGE_PASSWORD=REDACTED

#python ../drive-gforge.py --generate-select-options
#exit 0


python ../drive-gforge.py \
    --tracker 677 \
    --csvfile core.csv \
    --slug core \
    --do-creates \
    --do-updates

kill %1
