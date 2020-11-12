#!/bin/bash
set -ex

SCRIPT="Build graph-app-kit docker"
./hello-start.sh "$SCRIPT"

( cd ../../docker && docker-compose build )

./hello-end.sh "$SCRIPT"