# Developer Guide

These instructions are for contributing to this repository. See main README.md for usage.

## Manual

```bash
cd src/docker
docker-compose build
docker-compose up
```

## Test

### CI

CI will trigger on pushes to PRs

### Local

To test locally:

```bash
cd src/python
./bin/lint.sh
python3 -m pytest test
```

This is expected to change as full docker-based testing lands

### AWS

* Modify `src/bootstraps/core/graphistry.yml` on the checkout step do use the branch:  `git clone -b mybranch`
* Push your branch
* In CloudFormation, upload your modified `graphistry.yml``

## Aligned base versions

For faster AWS launches and Graphistry Enterprise, we:

- Keep the docker base in sync w/ AWS version & enterprise version:
  * docker-compose.yml: `GRAPHISTRY_FORGE_BASE_VERSION`
  * Dockerfile: `GRAPHISTRY_FORGE_BASE_VERSION`
  * Set both to the appropriate Graphistry (or sufficient Python) base, e.g., `v2.39.12-11.4`

- Update aws version (bootstraps/*/graphistry.yml) by pointing to that version's region AMIs via bootstraps/scripts/graphistry-ami-list.sh
  * Setup: `apt-get install awscli jq` and `aws configure`
  * Run `src/bootstraps/scripts $ VERSION=2.36.6-11.0 ./graphistry-ami-list.sh`
  * Paste into `src/bootstraps/core,neptune/graphistry.yml`
  * Update `src/docker/docker-compose.yml::GRAPHISTRY_FORGE_BASE_VERSION`

## DockerHub Automated Builds

Managed via DockerHub automates tagged builds

Ahead of time:

* Ensure you've set `GRAPHISTRY_FORGE_BASE_VERSION` in the `Dockerfile` (not just the `docker-compose.yml`)
* Merged into master

Publish:

1. `git tag 2.39.12`
  * Use a tag that corresponds to the Graphistry version, or some suffix (`2.39.12.1`)
  * Note lack of `v`
2. `git push --tags`

DockerHub automatic builds will:
* publish as tag `v2.39.12-11.4`: note addition of `v` and `-11.4`
* publish as tag `latest`

See [current tags](https://hub.docker.com/r/graphistry/graph-app-kit-st/tags) and available [base tags](https://hub.docker.com/r/graphistry/graphistry-forge-base/tags)

## AWS Publish action

* Docker rebuilds on merge to main
* Push main tag ('v1.2.3') for building named versions
* CloudFormation templates uploaded to S3 upon a PR being labeled "publish", merge-to-main, or explicit GHA call
