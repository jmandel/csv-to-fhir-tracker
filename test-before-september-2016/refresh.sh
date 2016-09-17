#!/bin/bash

cd ~/work/fhir-trunk-svn
svn update
cd -

cat ~/work/fhir-trunk-svn/ballots/2016-09\ STU\ 3/FHIR_R1_D3_2016SEP_amalgamated-cleaned.csv | \
iconv -f  ISO-8859-1 -t utf-8  > core.csv

cat ~/work/fhir-trunk-svn/ballots/2016-09\ STU\ 3/fluentpath/cleaned_master.csv | \
iconv -f  utf-8 -t utf-8  > /tmp/fluentpath.csv
dd if=/tmp/fluentpath.csv bs=1 skip=115 of=fluentpath.csv
