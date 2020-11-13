#!/bin/bash
set -ex

SCRIPT="Wait Graphistry docker containers healthy"
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

echo "--- Graphistry status after healthy waiting ---"
( cd "${GRAPHISTRY_HOME}" && sudo docker-compose ps )

./hello-end.sh "$SCRIPT"