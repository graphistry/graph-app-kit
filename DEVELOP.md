# Developer Guide

These instructions are for contributing to this repository. See main README.md for usage.


## Automated Builds

Managed via DockerHub automated builds

* Master merge updates tag `latest`
* Git tags publish to the DockerHub repo for each service
* Failed builds do not publish

See [current tags](https://hub.docker.com/repository/docker/graphistry/graph-app-kit-st)

## Publish

* Docker rebuilds on merge to main
* CloudFormation templates upload upon a PR being labeled "publish"

