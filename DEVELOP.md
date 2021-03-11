# Developer Guide

These instructions are for contributing to this repository. See main README.md for usage.

## Manual

```bash
cd src/docker
docker-compose build
docker-compose up
```

## Test

CI will trigger on pushes to PRs

To test locally:

```bash
cd src/python
./bin/lint.sh
python3 -m pytest test
```

This is expected to change as full docker-based testing lands

## Aligned base versions

For faster AWS launches, we:

- Keep the docker base (docker-compose.yml::GRAPHISTRY_FORGE_BASE_VERSION) in sync w/ AWS version

- Update aws version (bootstraps/*/graphistry.yml) by pointing to that version's region AMIs via bootstraps/scripts/graphistry-ami-list.sh
  * Run `src/bootstraps/scripts $ VERSION=2.36.6 ./graphistry-ami-list.sh`
  * Paste into `src/bootstraps/core,neptune/graphistry.yml`
  * Test via using branch's yml's url, or copy-paste into cloud formation

## Automated Builds

Managed via DockerHub automated builds

* Master merge updates tag `latest`
* Git tags ('v1.2.3') publish to the DockerHub repo for each service
* Failed builds do not publish

See [current tags](https://hub.docker.com/repository/docker/graphistry/graph-app-kit-st)

## Publish

* Docker rebuilds on merge to main
* Push main tag ('v1.2.3') for building named versions
* CloudFormation templates uploaded to S3 upon a PR being labeled "publish", merge-to-main, or explicit GHA call
