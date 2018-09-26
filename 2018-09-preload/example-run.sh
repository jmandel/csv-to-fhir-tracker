killall chromedriver
../chromedriver &

# python ../drive-gforge.py --generate-select-options
python ../drive-gforge.py \
    --tracker 677 \
    --csvfile ballotcomments_FHIR_R4_OBS_N2_2018SEP_clean.csv \
    --slug core-norm-observation

python ../drive-gforge.py \
    --tracker 677 \
    --csvfile ballotcomments_FHIR_R4_PATIENT_N2_2018SEP_clean.csv \
    --slug core-norm-patient
killall chromedriver
