#!/bin/bash
set -ex

SCRIPT="Install docker for AWS"
./hello-start.sh "$SCRIPT"

sudo amazon-linux-extras install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chkconfig docker on

./hello-end.sh "$SCRIPT"