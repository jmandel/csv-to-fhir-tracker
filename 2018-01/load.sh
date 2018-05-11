#!/bin/bash

../chromedriver &
#export GFORGE_USERNAME=fhir_bot
#export GFORGE_PASSWORD=REDACTED

#python ../drive-gforge.py --generate-select-options
#exit 0


#python ../drive-gforge.py --tracker 677 --csvfile core.csv --slug core --do-creates --do-updates
#python ../drive-gforge.py --tracker 677 --csvfile immunization.csv --slug immunizations --do-creates --do-updates
#python ../drive-gforge.py --tracker 677 --csvfile qicore.csv --slug qicore --do-creates --do-updates
#python ../drive-gforge.py --tracker 677 --csvfile uscore.csv --slug uscore --do-creates --do-updates
#python ../drive-gforge.py --tracker 677 --csvfile vhd.csv --slug vhd --do-creates --do-updates

#python ../drive-gforge.py --tracker 677 --csvfile ecr.csv --slug eCR --do-creates --do-updates

#TODO
python ../drive-gforge.py --tracker 677 --csvfile pocd.csv --slug PoCD --do-creates --do-updates
python ../drive-gforge.py --tracker 677 --csvfile phd.csv --slug phd --do-creates --do-updates

kill %1
