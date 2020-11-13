#!/bin/bash
set -e

### Minimal st setup
###  Assume empty AMI, Graphistry Hub

cd ../scripts

SCRIPT="Minimal graph-app-kit for Graphistry"
./hello-start.sh "$SCRIPT"

export GRAPHISTRY_USERNAME=$1
export GRAPHISTRY_PASSWORD=$2
export GRAPHISTRY_HOST=$3
export GRAPHISTRY_PROTOCOL=$4
export GAK_PUBLIC=/home/ec2-user/graph-app-kit/public/graph-app-kit

echo
echo "----- SETTINGS ------"
echo " * GRAPHISTRY_USERNAME (\$1): $GRAPHISTRY_USERNAME"
echo " * GRAPHISTRY_PASSWORD (\$2): ***"
echo " * GRAPHISTRY_HOST (\$3): $GRAPHISTRY_HOST"
echo " * GRAPHISTRY_PROTOCOL (\$4): $GRAPHISTRY_PROTOCOL"
echo " * GAK_PUBLIC: $GAK_PUBLIC"
echo "---------------------"
source instance-id.sh
echo " * INSTANCE_ID: $INSTANCE_ID"
echo

./docker-aws.sh
./docker-container-build.sh

echo '===== Configuring graph-app-kit with Graphistry account ====='
( \
    cd ../../docker \
    && echo "ST_PUBLIC_PORT=80" \
    && echo "BASE_PATH=public/dash/" \
    && echo "GRAPHISTRY_USERNAME=${GRAPHISTRY_USERNAME}" \
    && echo "GRAPHISTRY_PASSWORD=${GRAPHISTRY_PASSWORD}" \
    && echo "GRAPHISTRY_PROTOCOL=${GRAPHISTRY_PROTOCOL}" \
    && echo "GRAPHISTRY_SERVER=${GRAPHISTRY_HOST}" \
) | sudo tee ../../docker/.env

echo '----- Launching graph-app-kit as streamlit-pub:8501'
( \
  cd "${GAK_PUBLIC}/src/docker" \
  && sudo /usr/local/bin/docker-compose up -d streamlit \
)

./hello-end.sh "$SCRIPT"