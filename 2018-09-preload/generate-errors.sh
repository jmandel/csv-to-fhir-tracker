#!/bin/sh

./example-run.sh  | grep ERR | sort | uniq -c > errors.txt
