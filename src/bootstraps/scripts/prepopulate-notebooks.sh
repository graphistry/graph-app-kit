#!/bin/bash
set -ex

VIEWS_PATH="$1"
VIEW_FOLDER_NAME="$2"
NB_OWNER="$3"

SCRIPT="Prepopulating notebooks (${NOTEBOOKS_HOME}/${VIEWS_PATH}/${VIEW_FOLDER_NAME})"
./hello-start.sh "$SCRIPT"

echo "---- SETTINGS ----"
echo "* NOTEBOOKS_HOME: $NOTEBOOKS_HOME"
echo "* VIEWS_PATH: $VIEWS_PATH"
echo "* VIEW_FOLDER_NAME: $VIEW_FOLDER_NAME"
echo "* NB_OWNER: $NB_OWNER"

mkdir -p "${NOTEBOOKS_HOME}/${VIEWS_PATH}"
cp -r ../../python/views "${NOTEBOOKS_HOME}/${VIEWS_PATH}/${VIEW_FOLDER_NAME}"

sudo chown -R "${NB_OWNER}" "${NOTEBOOKS_HOME}/${VIEWS_PATH}"

./hello-end.sh "$SCRIPT"