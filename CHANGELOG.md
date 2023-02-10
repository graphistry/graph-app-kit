# Changelog

All notable changes to the graph-app-kit are documented in this file.

The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and all PyGraphistry-specific breaking changes are explictly noted here.

Related changelogs:

Core:
* [Streamlit](https://docs.streamlit.io/en/stable/changelog.html)
* [PyGraphistry changelog](https://github.com/graphistry/pygraphistry/blob/master/CHANGELOG.md)
* [Graphistry core changelog](https://graphistry.zendesk.com/hc/en-us/articles/360033184174-Enterprise-Release-List-Downloads)
* [RAPIDS changelog](https://github.com/rapidsai/cudf/releases)

Extensions:
* [Neo4j](https://neo4j.com/release-notes/)
* [TigerGraph](https://docs.tigergraph.com/faqs/change-log-1)
* [AWS Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/doc-history.html)

## [Development]

See [projects page](https://github.com/graphistry/graph-app-kit/projects) and [open pull requests](https://github.com/graphistry/graph-app-kit/pulls)

### Changed

* Infra: CUDA base now 11.5
* Infra: Optimized runner
* Infra: Remove now-unnecessary free space step

### Added

* Infra: env var USE_DOCKER=true
* Infra: env var PYTHONPATH=/apps/views
* Infra: env var FAVICON_URL
* Infra: externally overridable src/streamlit/{config.toml,credentials.toml}
* Infra: Update GPU base to 2.39.27
* Infra: Update actions/checkout GHA from v2 (deprecated) to v3

### Breaking

* Infra: Removed autoheal service and labels (likely OK for most users)

### Fixed

* toml: Fixed startup for users of new startup system (master)


## [2.39.25 - 2022.08.14]

### Changed

* Update dependency PyGraphistry 0.27.1
* Update dependency Streamlit to 1.12.0
* Update RAPIDS-ecosystem packages (2022.04)

## [2.39.13 - 2022.05.07]

### Added

* opt-in to minimal CPU-only base image 
* alias in `src/docker`: `./dc`, `./dc.cpu`
* test python 3.7, 3.8, 3.9
* test cpu and gpu docker building

### Changed

* build now uses buildkit
* minimal

### Docs

* cpu mode
* aliases of `./dc` and `./dc.cpu`

### Breaking

* Temporarily switch dockerhub build to CPU minimal while too-large base image kinks get worked out 

## [2022.03.13]

### Changed

* GraphistrySt: Switched from unsafe mode markdown to component
* PyGraphistry: Updated to 0.21.2

### Breaking

* UI: Switch default to wide mode


## [2022.03.02]

### Changed

* Infra: Upgrade to Graphistry 2.38.10 base
* Infra: Unpinned plotly and updated protobuf, streamlit

### Added

* Infra: New `docker-compose.override.yml` symlink mode (WIP)

### Fixed

* Infra: Replaced failing GHA collaborators-only with repo setting

## [2021.03.11]

### Changed

* CI: Graphistry AMI list generator takes VERSION parameter
* Infra: Upgrade to Graphistry 2.36.6

### Docs

* CI: Graphistry AMI list generator usage
* README: Removed dangling link
* README: Quicklaunch links and admin commands

### Fixed

* Private Streamlit dashboards instance now bound to Jupyter notebook private dashboards folder. Was incorrectly using the public folder: https://github.com/graphistry/graph-app-kit/pull/51/commits/3872de053b7d2888ce271acf395f112491742606

## [2021.03.06]

### Added

* CI: Publish cloud formation templates to s3 on merge (https://github.com/graphistry/graph-app-kit/pull/48)

## [2021.02.24]

#### Added

* TigerGraph support (https://github.com/graphistry/graph-app-kit/pull/36)

## [2021.02.23]

### Added

* Changelog
* AMI enumeration script
* Tests: flake8, docker build
* CI: GHA
* CI: Badges

### Changed

* Versions: Streamlit 0.70 -> 0.77, PyGraphistry 0.14 -> 0.17.2, Graphistry -> 2.35.9 (including AMIs)
* Dev docs: Tagging, building
* Graphistry 2.35+ Support: Swaps in old < 2.34-style Caddy 1.x container as Graphistry 2.35's Caddy 2.x is currently tricky for auth reuse
* Plotter auto-memoizes with `.plot(as_files=True, ...)`

### Fixed

* Flake8 warnings

### Breaking

* Default base container now CUDA 11.0

---
