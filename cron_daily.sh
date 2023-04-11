#!/bin/sh

# Get path of current shell script so it can be used to absolutely reference other local scripts
SCRIPT="$(readlink --canonicalize-existing "$0")"
SCRIPTPATH="$(dirname "$SCRIPT")"

echo "Running checking of Elsevier authentication tokens"
$SCRIPTPATH/venv/bin/python $SCRIPTPATH/scopuscheck.py

echo "Elsevier token checking finished"
