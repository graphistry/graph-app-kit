#!/bin/bash
set -e

### Full neptune/graphistry/st setup:
###  caddy, jupyter, pub/priv st, ...
### Assumes Graphistry GPU AMI: docker, ...

cd ../scripts

SCRIPT="Full graph-app-kit for Neptune/Graphistry"
./hello-start.sh "$SCRIPT"

export GRAPHISTRY_HOME=${GRAPHISTRY_HOME:-/home/ubuntu/graphistry}
export NOTEBOOKS_HOME=${NOTEBOOKS_HOME:-${GRAPHISTRY_HOME}/data/notebooks}
export NEPTUNE_READER_HOST=$1
export GAK_PUBLIC=/home/ubuntu/graph-app-kit/public/graph-app-kit
export GAK_PRIVATE=/home/ubuntu/graph-app-kit/private/graph-app-kit

echo
echo "----- SETTINGS ------"
echo " * GRAPHISTRY_HOME: $GRAPHISTRY_HOME"
echo " * NOTEBOOKS_HOME: $NOTEBOOKS_HOME"
echo " * NEPTUNE_READER_HOST (\$1): $NEPTUNE_READER_HOST"
echo "---------------------"
source instance-id.sh
echo " * INSTANCE_ID: $INSTANCE_ID"
echo

./cloudformation-bootstrap.sh
./docker-container-build.sh
./prepopulate-notebooks.sh graph-app-kit/public views ubuntu
./prepopulate-notebooks.sh graph-app-kit/private views ubuntu
./graphistry-wait-healthy.sh
./swap-caddy.sh
source ./graphistry-service-account.sh
echo "Got SERVICE_USER ${SERVICE_USER}, SERVICE_PASS"

echo '===== Configuring graph-app-kit with Graphistry service account and Neptune ====='
( \
    cd ../../docker \
    && echo "GRAPH_VIEWS=${GRAPHISTRY_HOME}/data/notebooks/graph-app-kit/public/views" \
    && echo "GRAPHISTRY_USERNAME=${SERVICE_USER}" \
    && echo "GRAPHISTRY_PASSWORD=${SERVICE_PASS}" \
    && echo "GRAPHISTRY_PROTOCOL=http" \
    && echo "GRAPHISTRY_SERVER=`curl http://169.254.169.254/latest/meta-data/public-ipv4`" \
    && echo "NEPTUNE_READER_PROTOCOL=wss" \
    && echo "NEPTUNE_READER_PORT=8182" \
    && echo "NEPTUNE_READER_HOST=$NEPTUNE_READER_HOST" \
) | sudo tee ../../docker/.env

echo '----- Reuse public graph-app-kit .env as private .env'
sudo cp "${GAK_PUBLIC}/src/docker/.env" "${GAK_PRIVATE}/src/docker/.env"

echo '----- Finish pub vs. priv .env specialization'
echo "BASE_PATH=public/dash/" | sudo tee -a "${GAK_PUBLIC}/src/docker/.env"
echo "BASE_PATH=private/dash/" | sudo tee -a "${GAK_PRIVATE}/src/docker/.env"

echo '----- Launching graph-app-kit as streamlit-pub/priv:8501'
( \
  cd "${GAK_PUBLIC}/src/docker" \
  && sudo docker-compose -p pub run -d --name streamlit-pub streamlit \
)
( \
  cd "${GAK_PRIVATE}/src/docker" \
  && sudo docker-compose -p priv run -d --name streamlit-priv streamlit \
)

./hello-end.sh "$SCRIPT"