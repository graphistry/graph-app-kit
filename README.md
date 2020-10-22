![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/graphistry/graph-app-kit-st)

# Welcome to graph-app-kit

Turn your graph data into a secure and interactive visual graph app in 15 minutes! 


![Screenshot](https://user-images.githubusercontent.com/4249447/92298596-8e518600-eeff-11ea-8276-069281a4af93.png)

## Why

This open source effort puts together patterns the Graphistry team has reused across many graph projects as teams went from Jupyter notebook experiments to deployed analyst tools. Whether building your first graph app, trying an idea,  or wanting to check a reference, this project aims to simplify the process. This means covering pieces like: Easy code editing and deployment, a project stucture ready for teams, built-in authentication, no need for custom JS/CSS at the start, batteries-included dependencies, and fast loading & visualization of large graphs.

## The pieces

`graph-app-kit` combines several emerging and best-of-class data technologies to get you going.

### Core stack

* Prebuilt Python project structure ready for prototyping
* [StreamLit](https://www.streamlit.io/) for quick self-serve dashboarding
* [Graphistry](https://www.graphistry.com/get-started) for point-and-click GPU-accelerated visual graph analytics
* Data frames: Data wrangling via [Pandas](https://pandas.pydata.org/), [Apache Arrow](https://arrow.apache.org/), [RAPIDS](https://rapids.ai/) (ex: [cuDF](https://github.com/rapidsai/cudf)), including handling formats such as CSV, XLS, JSON, Parquet, and more
* Docker and docker-compose for easy cross-platform deployment & management

### Prebuilt integrations & recipes

* Graph databases
  
  * [TinkerPop Gremlin](https://tinkerpop.apache.org/) connector demos:
    * [AWS Neptune](https://aws.amazon.com/neptune/)

  * Collaborations welcome!

* [Jupyter notebooks](https://jupyter.org/): Volume mount recipe for sharing code so code can be live-edited

* [Caddy](https://caddyserver.com/): Reverse proxy for custom URLs, [automatic LetsEncrypt TLS certificates](http://letsencrypt.org/), multiple sites on the same domain, pluggable authentication

## Get going

Most commands can be run from folder `src/docker`:

### Download

```
git clone https://github.com/graphistry/graph-app-kit.git
```

### Build

```
cd src/docker
docker-compose build
```

### Start & stop


`cd src/docker` and then:

* Start: `docker-compose up -d`
* Use: Go to `http://localhost:8501/dashboard`
* Stop: `docker-compose down -v`

### Logs

By default, Docker json file driver: `docker-compose logs -f -t --tail=100`

### Live edit

* Modify Python files in `src/python/views/[your dashboard]/__init__.py`, and in-tool, hit the `rerun` button that appears
* Add new views by adding `views/[your dsahboard]/__init__.py` with methods `def info(): return {'name': 'x'}` and `def run(): None`
* Add new dependencies: modify `src/python/requirements-app.txt` and rerun `docker-compose build` and restart

## GPU-ready (Optional)

The containers can take advantage of GPUs when present and the host operating system enables the [Nvidia runtime for Docker](https://github.com/NVIDIA/nvidia-docker). The `graph-app-kit` Docker container is ready for:

* GPU Analytics:  [RAPIDS](https://www.rapids.ai) and CUDA already setup
* GPU Visualization: Connect to an external Graphistry instance or run on the same node

### Configure

Most settings can be set by creating a custom Docker environment file `src/docker/.env` (see `src/envs/*.env` for options). You can also edit `docker-compose.yml` and `/etc/docker/daemon.json`, but we recommend sticking to `.env`.


**Core:**
* StreamLit: URL base path: `BASE_PATH=dashboard/` and `BASE_URL=http://localhost/dashboard/`
* Graphistry: None - set `GRAPHISTRY_USERNAME=usr` + `GRAPHISTRY_PASSWORD=pwd` (see `src/envs/graphistry.env` for more, like `GRAPHISTRY_SERVER` if using a private Graphistry server)
* Log level: `LOG_LEVEL=ERROR` (for Python's `logging`)

**Integrations:**
* [Amazon Neptune guide](docs/neptune.md) for TinkerPop/Gremlin integration
* [Caddy sample](src/caddy/Caddyfile) for reverse proxying


### Toggle views

Configure which dashboards `AppPicker` includes:

* Disable individual dashboards: Have a dashboard's `info()` return `{'enabled': False}`
* Create tags and toggle them: 
  * Tag a dashboard view as part of `src/python/views/[your_app]/__init__.py`:
     * `info()`: `{'tags': ['new_app', ...]}`
  * Opt-in and opt-out to tags: in `src/python/entrypoint.py`:
    * `AppPicker(include=['testing', 'new_app'], exclude=['demo'])`

### WIP:
* Support both private + public dashboards
* Free TLS certificates: Modify `Caddyfile` with your domain name
* Reuse your auth provider: Modify `Caddyfile` with your JWT etc. auth check URL

## Contribute

We welcome all sorts of help!

* Deployment: Docker, cloud runners, ...
* Dependencies: Common graph packages
* Connectors: Examples for common databases and how to get a lot of data out
* Demos!

See [develop.md](develop.md) for more information
