![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/graphistry/graph-app-kit-st)

# Welcome to graph-app-kit

Turn your graph data into a secure and interactive visual graph app in 15 minutes! 


![Screenshot](https://user-images.githubusercontent.com/4249447/92298596-8e518600-eeff-11ea-8276-069281a4af93.png)

## Why

This open source effort puts together patterns the Graphistry team has reused across many graph projects as teams went from Jupyter notebook experiments to deployed analyst tools. Whether building your first graph app, trying an idea,  or wanting to check a reference, this project aims to simplify the process. This means covering pieces like: Easy code editing and deployment, a project stucture ready for teams, built-in authentication, no need for custom JS/CSS at the start, batteries-included dependencies, and fast loading & visualization of large graphs.

## The pieces

`graph-app-kit` combines several emerging and best-of-class data technologies to get you going:

* Prebuilt Python project structure ready for prototyping
* [StreamLit](https://www.streamlit.io/) for quick self-serve dashboarding
* [Graphistry](https://www.graphistry.com/get-started) for point-and-click GPU-accelerated visual graph analytics
* Python connectors for your favorite data sources
   * [TinkerPop Gremlin](https://tinkerpop.apache.org/) connector (ex: [AWS Neptune](https://aws.amazon.com/neptune/))
   * Data frames: [Pandas](https://pandas.pydata.org/), [Apache Arrow](https://arrow.apache.org/), [RAPIDS](https://rapids.ai/) (ex: [cuDF](https://github.com/rapidsai/cudf)), including reading formats such as CSV, XLS, JSON, Parquet, and more
* Docker and docker-compose for easy cross-platform deployment & management
* [Caddy](https://caddyserver.com/) reverse proxy for custom URLs, [automatic LetsEncrypt TLS certificates](http://letsencrypt.org/), pluggable authentication
* Volume mounts for opening in live web code editors like [Jupyter notebooks](https://jupyter.org/)


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

* Start: `docker-compose up -d`
* Use: Go to `http://localhost:8501/dashboard`
* Stop: `docker-compose down -v`

### Logs

By default, Docker json file driver: `docker-compose logs -f -t --tail=100`

### Live edit

* Modify Python files in `src/python/views/`, and in-tool, hit the `rerun` button that appears
* Add new views by adding `apps/<my_app>/__init__.py` with methods `def info(): return {'name': 'x'}` `def run(): None`
* Add new dependencies: modify `src/python/requirements-app.txt` and rerun `docker-compose build`

## GPU-ready

The containers can take advantage of GPUs when present and the host operating system enables the [Nvidia runtime for Docker](https://github.com/NVIDIA/nvidia-docker). The `graph-app-kit` Docker container is ready for:

* GPU Analytics:  [RAPIDS](https://www.rapids.ai) and CUDA already setup
* GPU Visualization: Connect to an external Graphistry instance or run on the same node

### Configure

Most settings can be set by creating a custom Docker environment file `src/docker/.env` (see `src/envs/*.env` for defaults):

* URL base path: `BASE_PATH=my_subpath/` (default `dashboard/`) and `BASE_URL=http://site.com/my_subpath/` (default `http://localhost:8501/dashboard`)
* Graphistry: `GRAPHISTRY_USERNAME=usr` + `GRAPHISTRY_PASSWORD=pwd` (see `src/envs/graphistry.env` for more, like `GRAPHISTRY_SERVER`)
* Log level: `LOG_LEVEL=DEBUG` (default `ERROR`)
* Neptune: Set options in `envs/neptune.env`, and optionally, run through a tunnel outside of the VPC

Advanced edits may also happen in `docker-compose.yml` and `/etc/docker/daemon.json` . 

### Toggle views

Configure which dashboards `AppPicker` includes:

* Disable individual dashboards: Have a dashboard's `info()` return `{'enabled': False}`
* Create tags and toggle them: 
  * Tag a dashboard view its `info()`: `{'tags': ['demo', ...]}`
  * Opt-in to tags: `AppPicker(include=['demo', 'demo_rapids'])`
  * Out-out of tags: `AppPicker(exclude=['demo_basic'])`


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
