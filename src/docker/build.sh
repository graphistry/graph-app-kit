#!/bin/bash

# This file will buld the local docker image for graph-app-kit
#
# It's assumed you checked out the repo with: 
#	git clone https://github.com/graphistry/graph-app-kit.git
# 	cd graph-app-kit/src/docker
#       ./build.sh
#
# Enable docker buildkit
# ... or run docker compose via provided alias script `./dc`
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build
./dc build

# Optional: Edit src/docker/.env (API accounts), docker-compose.yml: Auth, ports, ...

# Launch
./dc up -d

echo "To optionally view logs for running container: ./dc logs -f -t --tail=100"

echo "To view the streamlit app navigate to http://localhost:8501"

