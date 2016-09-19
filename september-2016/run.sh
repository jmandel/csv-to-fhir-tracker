/tmp/chromedriver &

GFORGE_USERNAME=fhir_bot
GFORGE_PASSWORD=redacted

# First, regenerate the selection options from any existing issue (e.g. 10000)

python ../drive-gforge.py --generate-select-options-from 10000


# Then, load ballot comments into tracker
python drive-gforge.py \
    --tracker 677 \
    --csvfile core.csv \
    --slug core
