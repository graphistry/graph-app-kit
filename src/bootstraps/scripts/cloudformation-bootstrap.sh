#!/bin/bash
set -ex

SCRIPT="Installing CloudFormation Bootstrap"
./hello-start.sh "$SCRIPT"

sudo apt-get update -y
sudo apt-get install -y python3-pip python-setuptools
sudo mkdir -p /opt/aws/bin
#sudo python /usr/lib/python2.7/dist-packages/easy_install.py --script-dir /opt/aws/bin https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
sudo wget -O /opt/aws-cfn-bootstrap-py3-latest.tar.gz https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-py3-latest.tar.gz

sudo tar zxvf aws-cfn-bootstrap-py3-latest.tar.gz 

sudo ln -s /opt/aws-cfn-bootstrap-2.0/init/ubuntu/cfn-hup /etc/init.d/cfn-hup

pip3 install aws-cfn-bootstrap-py3-latest.tar.gz

./hello-end.sh "$SCRIPT"
