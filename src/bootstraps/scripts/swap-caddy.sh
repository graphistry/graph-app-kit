#!/bin/bash
set -ex

## Graphistry now uses Caddy2, and until Caddy 2 supports simple auth, g-a-k still sticks with Caddy1
## ... So we stop Graphistry's Caddy 2  and put in a docker-compose of its old

CADDY_FILENAME=${CADDY_FILENAME:-full.Caddyfile}
CADDY_COMPOSE_FILENAME=${CADDY_COMPOSE_FILENAME:-docker-compose.gak.graphistry.yml}

SCRIPT="Swap Caddyfile"
./hello-start.sh "$SCRIPT"

echo "* Using CADDY_FILENAME: $CADDY_FILENAME"

sudo cp "../../caddy/${CADDY_COMPOSE_FILENAME}" "${GRAPHISTRY_HOME}/${CADDY_COMPOSE_FILENAME}"
sudo cp "../../caddy/${CADDY_FILENAME}" "${GRAPHISTRY_HOME}/data/config/Caddyfile"
( \
    cd "${GRAPHISTRY_HOME}" \
    && sudo docker-compose stop caddy \
    && sudo docker-compose -f "${CADDY_COMPOSE_FILENAME}" up -d caddy \
    && sudo docker-compose ps \
    && sudo docker-compose -f "${CADDY_COMPOSE_FILENAME}" ps \
)

./hello-end.sh "$SCRIPT"