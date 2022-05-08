#!/bin/bash
set -ex

SCRIPT="Build graph-app-kit docker"
DC_ALIAS=${DC_ALIAS:-docker-compose}
./hello-start.sh "$SCRIPT"

( cd ../../docker && $DC_ALIAS build )

./hello-end.sh "$SCRIPT"