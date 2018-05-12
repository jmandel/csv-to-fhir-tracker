#!/bin/bash

../chromedriver &

#export GFORGE_USERNAME=fhir_bot
#export GFORGE_PASSWORD=REDACTED

for i in core-norm-patient.csv; do
    python ../drive-gforge.py \
        --tracker 677 \
        --csvfile  $i \
        --slug ${i%.csv} \
        --do-creates \
        --do-updates
done

kill %1
