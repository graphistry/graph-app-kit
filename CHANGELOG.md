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

### Adding

* TigerGraph


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
