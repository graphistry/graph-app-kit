#!/bin/bash
set -ex

SCRIPT="Build graph-app-kit docker"
./hello-start.sh "$SCRIPT"


( \
  cd "${GRAPHISTRY_HOME}" \
  && for i in `sudo docker-compose ps --services`; do ( \
    ( \
        until ( \
          [[ '"healthy"' == $(sudo docker inspect "graphistry_${i}_1" --format "{{json .State.Health.Status}}") ]] \
        ); do ( \
        echo "waiting on $i (5s)" \
        && sudo docker-compose ps \
        && sleep 5 \
        ); done \
    ) && echo "healthy $i" \
  ); done \
)

sudo docker-compose ps

./hello-end.sh "$SCRIPT"