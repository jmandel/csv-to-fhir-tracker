/tmp/chromedriver &

GFORGE_USERNAME=fhir_bot
GFORGE_PASSWORD=redacted

# First, regenerate the selection options from any existing issue (e.g. 1063)

python ../drive-gforge.py --generate-select-options-from 1063


# Then, load ballot comments into test tracker (1043)
python drive-gforge.py \
    --tracker 1043 \
    --csvfile core.csv \
    --slug core \
    --do-updates \
    --do-creates
