#!/bin/bash
set -ex

SCRIPT="Install docker for AWS"
./hello-start.sh "$SCRIPT"

sudo amazon-linux-extras install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chkconfig docker on

sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version

./hello-end.sh "$SCRIPT"