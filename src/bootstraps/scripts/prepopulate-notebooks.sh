#!/bin/bash
set -ex

VIEWS_PATH="$1"
VIEW_FOLDER_NAME="$2"

SCRIPT="Prepopulating notebooks (${NOTEBOOKS_HOME}/${VIEWS_PATH}/${VIEW_FOLDER_NAME})"
./hello-start.sh "$SCRIPT"

echo "* Using NOTEBOOKS_HOME: $NOTEBOOKS_HOME"

mkdir -p "${NOTEBOOKS_HOME}/${VIEWS_PATH}"
cp -r ../../python/views "${NOTEBOOKS_HOME}/${VIEWS_PATH}/${VIEW_FOLDER_NAME}"

./hello-end.sh "$SCRIPT"