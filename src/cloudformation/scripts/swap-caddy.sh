#!/bin/bash
set -ex

CADDY_FILENAME=${CADDY_FILENAME:-full.Caddyfile}

SCRIPT="Swap Caddyfile"
./hello-start.sh "$SCRIPT"

echo "* Using CADDY_FILENAME: $CADDY_FILENAME"

sudo cp "../../caddy/${CADDY_FILENAME}" "${GRAPHISTRY_HOME}/data/config/Caddyfile"
( \
    cd "${GRAPHISTRY_HOME}" \
    && sudo docker-compose up -d --force-recreate caddy \
    && sudo docker-compose ps \
)

./hello-end.sh "$SCRIPT"