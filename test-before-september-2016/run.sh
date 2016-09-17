/tmp/chromedriver &

GFORGE_USERNAME=fhir_bot
GFORGE_PASSWORD=redacted

# First, regenerate the selection options from any existing issue (e.g. 10000)

python ../drive-gforge.py --generate-select-options-from 10000


# Then, load ballot comments into test tracker (1052)
python drive-gforge.py \
    --tracker 1052 \
    --csvfile core-new.csv \
    --slug core
