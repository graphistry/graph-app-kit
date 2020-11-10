# Configure graph-app-kit and add integrations

Most settings can be configured by creating a custom Docker environment file `src/docker/.env` (see `src/envs/*.env` for options). You can also edit `docker-compose.yml` and `/etc/docker/daemon.json`, but we recommend sticking to `.env`.

Integration settings that deal with external systems such as TLS, accounts, and notebooks require having launched them. If you are not integrating into existing ones, see the initial [setup section](setup.md) for how to quicklaunch a Graphistry server.

## Monitoring

By default, `graph-app-kit` logging uses the Docker json file driver:

* Inspect recent activities: `cd src/docker` and then `sudo docker-compose logs -f -t --tail=100`

* Setup [alternative logging drivers](https://docs.docker.com/config/containers/logging/configure/)

## Core

* Streamlit: URL base path: `BASE_PATH=dashboard/` and `BASE_URL=http://localhost/dashboard/`
* Graphistry: None - set `GRAPHISTRY_USERNAME=usr` + `GRAPHISTRY_PASSWORD=pwd` (see `src/envs/graphistry.env` for more, like `GRAPHISTRY_SERVER` if using a private Graphistry server)
* Log level: `LOG_LEVEL=ERROR` (for Python's `logging`)

## Databases

* [Amazon Neptune guide](docs/neptune.md) for TinkerPop/Gremlin integration

## TLS with Cadddy

* Auth: See [Caddy sample](src/caddy/Caddyfile) reverse proxy example for an authentication check against an account system, including the one shipping with your Graphistry server (requires `sudo docker-compose restart caddy` in your Graphistry server upon editing `/var/graphistry/data/config/Caddyfile`)

## Public+Private views
* To simulatenously run 1 public and 1 private instance, create two `graph-app-kit` clones `public_dash` and `private_dash`, and for `src/docker/.env`, set:
  * `COMPOSE_PROJECT_NAME=streamlit-pub` and `COMPOSE_PROJECT_NAME=streamlit-priv`
  * Override default `ST_PUBLIC_PORT=8501` with two distinct values
* See [Caddy sample](src/caddy/Caddyfile) for configuring URI routes, including covering the private instance with your Graphistry account system (JWT auth URL)