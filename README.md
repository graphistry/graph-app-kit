![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/graphistry/graph-app-kit-st)

# Welcome to graph-app-kit

Turn your graph data into a secure and interactive visual graph app in 15 minutes! 

This open source effort puts together patterns the Graphistry team has reused across many graph projects as teams went from Jupyter notebook experiments to deployed analyst tools. This means ideas like: Easy code editing and deployment, a project stucture ready for teams, built-in authentication, no need for custom JS/CSS at the start, batteries-included dependencies, and fast loading & visualization of large graphs.

## The idea

Going from graph data to an interactive graph app just got a lot easier. This starter kit combines several emerging and best-of-class data technologies to get you going:

* Prebuilt Python project structure ready for prototyping
* StreamLit for quick self-serve dashboarding
* Graphistry for point-and-click GPU-accelerated visual graph analytics
* Python connectors for your favorite data sources
   * TinkerPop Gremlin connector (ex: AWS Neptune)
   * DataFrames: Pandas, Apache Arrow, RAPIDS (cuDF)
* Docker and docker-compose for easy cross-platform deployment & management
* Caddy reverse proxy for custom URLs, automatic LetsEncrypt TLS certificates, pluggable authentication
* Volume mounts for opening in live web code editors like Jupter notebooks


## Get going

### Build

`docker-compose build`

### Start & stop

* Start: `docker-compose up -d`
* Use: Go to `http://localhost` (or `http://localhost/<subpath>`)
* Stop: `docker-compose down -v`

### Live edit

* Modify Python files in `apps/`, and in-tool, hit the `rerun` button that appears
* Add new views by adding `apps/<my_app>/__init__.py` with methods `def info(): return {'name': 'x'}` `def run(): None`
* Add new dependencies: modify `requirements.txt` and rerun `docker-compose build`

### Configure

* Custom subpath: Modify commented areas of `docker-compose.yml` and `Caddyfile`
* Free TLS certificates: Modify `Caddyfile` with your domain name
* Reuse your auth provider: Modify `Caddyfile` with your JWT etc. auth check URL
* Support both private + public dashboards

## GPU-ready

* Wrangling: Set the docker-compose.yml's base image line to RAPIDS 
* Visualization: Connect to an external Graphistry instance or run on the same node

## Contribute

We welcome all sorts of help!

* Deployment: Docker, cloud runners, ...
* Dependencies: Common graph packages
* Connectors: Examples for common databases and how to get a lot of data out
* Demos!
