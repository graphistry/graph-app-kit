#!/bin/bash
set -ex

SCRIPT="Installing CloudFormation Bootstrap"
./hello-start.sh "$SCRIPT"

sudo apt-get update -y
sudo apt-get install -y python-pip python-setuptools
sudo mkdir -p /opt/aws/bin
sudo python /usr/lib/python2.7/dist-packages/easy_install.py --script-dir /opt/aws/bin https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz

./hello-end.sh "$SCRIPT"