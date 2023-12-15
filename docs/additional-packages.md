# Adding Custom Python Packages to graph-app-kit

## Install Custom Python Packages Locally

Install the desired custom Python packages on your localhost.  For example, if you want to include a different version of `pygraphistry` and an additional dependency like `faker`, run the following commands in your terminal:

```bash
pip install pip install graphistry[all] -t /home/user/additional-python-packages
pip install faker -t /home/user/additional-python-packages
```

## Mount the Volume in Docker Compose

Update your Docker Compose file to mount the volume to the GAK container.  Specify the path to your local directory and the desired mount point inside the container in the environment variable `ADDITIONAL_PYTHON_PATH` (`/mnt` in this example):

```yaml
services:
  streamlit:
    <<: *production_opts
    image: graphistry/graph-app-kit-st:${DOCKER_TAG:-latest}-${CUDA_SHORT_VERSION:-11.5}
    command: --server.baseUrlPath="$BASE_PATH" /apps/entrypoint.py
    build:
      <<: *build_kwargs
      context: ..
      dockerfile: ./docker/Dockerfile
      cache_from:
        - graphistry/graph-app-kit-st:${DOCKER_TAG:-latest}-${CUDA_SHORT_VERSION:-11.5}
    ports:
      - "${ST_PUBLIC_PORT:-8501}:8501"
    volumes:
      - ../python:/apps
      - ${GRAPH_VIEWS:-../python/views}:/apps/views
      - ${NEPTUNE_KEY_PATH:-/tmp/mt.pem}:/secrets/neptune-reader.pem
      - ../streamlit/config.toml:/root/gak/config.toml
      - ../streamlit/credentials.toml:/root/gak/credentials.toml
      - /home/user/additional-python-packages:/mnt:ro
    environment:
        ADDITIONAL_PYTHON_PATH: "/mnt"
    healthcheck:
      test:
        [
          "CMD",
          "curl",
          "-Lf",
          "http://localhost:8501/${BASE_PATH}healthz"
        ]
      interval: 30s
      timeout: 30s
      retries: 10
      start_period: 10s
```

Note that we just added these lines to the original service definition:
```yaml
services:
  streamlit:
    ...
    volumes:
      ...
      - /home/user/additional-python-packages:/mnt:ro
    environment:
        ADDITIONAL_PYTHON_PATH: "/mnt"
    ...
```

That's it! You've successfully added custom Python packages to the graph-app-kit container.  You can now use these packages in your GAK environment for graph analytics and visualizations.
