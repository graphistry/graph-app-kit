![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/graphistry/graph-app-kit-st)

[<img src="https://img.shields.io/badge/slack-Graphistry%20chat-yellow.svg?logo=slack">](https://join.slack.com/t/graphistry-community/shared_invite/zt-53ik36w2-fpP0Ibjbk7IJuVFIRSnr6g) 
![Twitter Follow](https://img.shields.io/twitter/follow/graphistry)

# Welcome to graph-app-kit

Turn your graph data into a secure and interactive visual graph app in 15 minutes! 


![Screenshot](https://user-images.githubusercontent.com/4249447/92298596-8e518600-eeff-11ea-8276-069281a4af93.png)

## Why

This open source effort puts together patterns the Graphistry team has reused across many graph projects as teams went from Jupyter notebook experiments to deployed analyst tools. Whether building your first graph app, trying an idea,  or wanting to check a reference, this project aims to simplify the process. This means covering pieces like: Easy code editing and deployment, a project stucture ready for teams, built-in authentication, no need for custom JS/CSS at the start, batteries-included dependencies, and fast loading & visualization of large graphs.

## Get started

### Quick

```bash
git clone https://github.com/graphistry/graph-app-kit.git
cd graph-app-kit/src/docker
sudo docker-compose build
# Optional: edit src/docker/.env, docker-compose.yml: Auth, ports, ...
sudo docker-compose up -d
sudo docker-compose logs -f -t --tail=100
# Add src/python/views/your_custom_view/__init__.py
```

### Guides

1. [Quick launch](docs/setup.md): Preintegrated Docker, Graphistry, Streamlit, Jupyter, RAPIDS.ai (GPU)
  * Variants: [manual launch](docs/setup-manual.md), [Amazon Neptune](docs/neptune.md)
2. [Add views](docs/views.md)
3. [Main configurations and extensions](docs/extend.md): Database connectors, authentication, notebook-based editing, and more

## The pieces

### Core

* Prebuilt Python project structure ready for prototyping
* [Streamlit](https://www.streamlit.io/) quick self-serve dashboarding
* [Graphistry](https://www.graphistry.com/get-started) point-and-click GPU-accelerated visual graph analytics
* Data frames: Data wrangling via [Pandas](https://pandas.pydata.org/), [Apache Arrow](https://arrow.apache.org/), [RAPIDS](https://rapids.ai/) (ex: [cuDF](https://github.com/rapidsai/cudf)), including handling formats such as CSV, XLS, JSON, Parquet, and more
* Standard Docker and docker-compose cross-platform deployment

### GPU acceleration (optional)

If GPUs are present, `graph-app-kit` leverages GPU cloud acceleration:

* GPU Analytics:  [RAPIDS](https://www.rapids.ai) and CUDA already setup for use if run with an Nvidia docker runtime - cudf GPU dataframes, [BlazingSQL](https://www.blazingsql.com) GPU SQL, cuGraph GPU graph algorithms, cuML libraries, and more

* GPU Visualization: Connect to an external Graphistry server or, faster, run on the same GPU server

### Prebuilt integrations & recipes

`graph-app-kit` works well with the Python data ecosystem (pandas, cudf, PySpark, SQL, ...) and we're growing the set of builtins and recipes:

* Graph databases
  
  * [AWS Neptune](https://aws.amazon.com/neptune/) ([quick launch](docs/neptune.md) and [manual launch](docs/neptune-manual.md))
  * [TinkerPop Gremlin](https://tinkerpop.apache.org/) ([query demos](https://github.com/graphistry/graph-app-kit/tree/master/src/python/views/demo_neptune_01_minimal_gremlin))

  * Collaborations welcome!

* [Jupyter notebooks](https://jupyter.org/): Volume mount recipe for sharing code so code can be live-edited (see [integrations guide](docs/extend.md))

* [Caddy](https://caddyserver.com/): Reverse proxy for custom URLs, [automatic LetsEncrypt TLS certificates](http://letsencrypt.org/), multiple sites on the same domain, pluggable authentication (see [integrations guide](docs/extend.md))


## Contribute

We welcome all sorts of help!

* Deployment: Docker, cloud runners, ...
* Dependencies: Common graph packages
* Connectors: Examples for common databases and how to get a lot of data out
* Demos!

See [develop.md](develop.md) for more contributor information
