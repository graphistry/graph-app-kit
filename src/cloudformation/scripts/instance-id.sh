#!/bin/bash
set -ex

SCRIPT="Get AWS Instance ID"
./hello-start.sh "$SCRIPT"

export INSTANCE_ID=$( curl -s http://169.254.169.254/latest/meta-data/instance-id )
echo "Exported INSTANCE_ID: $INSTANCE_ID"

./hello-end.sh "$SCRIPT"