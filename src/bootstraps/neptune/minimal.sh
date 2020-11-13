#!/bin/bash
set -ex

### Full neptune/graphistry/st setup:
###  caddy, jupyter, pub/priv st, ...
### Assumes Graphistry GPU AMI: docker, ...

cd ../scripts

SCRIPT="Minimal graph-app-kit for Neptune/Graphistry"
./hello-start.sh "$SCRIPT"

export NEPTUNE_READER_HOST=$1
export GRAPHISTRY_USERNAME=$2
export GRAPHISTRY_PASSWORD=$3
export GRAPHISTRY_HOST=$4
export GRAPHISTRY_PROTOCOL=$5
export GAK_PUBLIC=/home/ec2-user/graph-app-kit/public/graph-app-kit

echo
echo "----- SETTINGS ------"
echo " * NEPTUNE_READER_HOST (\$1): $NEPTUNE_READER_HOST"
echo " * GRAPHISTRY_USERNAME (\$2): $GRAPHISTRY_USERNAME"
echo " * GRAPHISTRY_PASSWORD (\$3): ***"
echo " * GRAPHISTRY_HOST (\$4): $GRAPHISTRY_HOST"
echo " * GRAPHISTRY_PROTOCOL (\$5): $GRAPHISTRY_PROTOCOL"
echo " * GAK_PUBLIC: $GAK_PUBLIC"
echo "---------------------"
source instance-id.sh
echo " * INSTANCE_ID: $INSTANCE_ID"
echo

./cloudformation-bootstrap.sh
./docker-aws.sh
./docker-container-build.sh

echo '===== Configuring graph-app-kit with Graphistry account and Neptune ====='
( \
    cd ../../docker \
    && echo "BASE_PATH=public/dash/" \
    && echo "GRAPHISTRY_USERNAME=${GRAPHISTRY_USERNAME}" \
    && echo "GRAPHISTRY_PASSWORD=${GRAPHISTRY_PASSWORD}" \
    && echo "GRAPHISTRY_PROTOCOL=${GRAPHISTRY_PROTOCOL}" \
    && echo "GRAPHISTRY_SERVER=${GRAPHISTRY_HOST}" \
    && echo "NEPTUNE_READER_PROTOCOL=wss" \
    && echo "NEPTUNE_READER_PORT=8182" \
    && echo "NEPTUNE_READER_HOST=$NEPTUNE_READER_HOST" \
) >> ../../docker/.env

echo '----- Config:'
cat ../../docker/.env

echo '----- Launching graph-app-kit as streamlit-pub:8501'\
( \
  cd "${GAK_PUBLIC}/src/docker" \
  && sudo docker-compose -p pub run -d --name streamlit-pub streamlit \
)

./hello-end.sh "$SCRIPT"