GFORGE_USERNAME=fhir_bot \
GFORGE_PASSWORD=redacted \
python drive-gforge.py \
    --tracker 677 \
    --csvfile may-2015/core.csv \
    --slug core \
    --do-updates \
    --do-creates
