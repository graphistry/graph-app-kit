# Default to big image, but allow thin cpu override
ARG DOCKER_TAG=latest
ARG GRAPHISTRY_FORGE_BASE_VERSION=v2.39.14-11.4
ARG PYTHON_VERSION=3.8
ARG BASE_IMAGE=graphistry/graphistry-forge-base:${GRAPHISTRY_FORGE_BASE_VERSION}
FROM python:$PYTHON_VERSION as cpu_base

ARG DOCKER_TAG=latest
ARG GRAPHISTRY_FORGE_BASE_VERSION=v2.39.14-11.4
ARG BASE_IMAGE=graphistry/graphistry-forge-base:${GRAPHISTRY_FORGE_BASE_VERSION}
FROM $BASE_IMAGE

EXPOSE 8501

# making directory of app
WORKDIR /app

COPY python/conda-app.sh ./
RUN { source activate rapids || echo ok ; } && ./conda-app.sh

COPY python/requirements-system.txt ./
RUN --mount=type=cache,target=/root/.cache \
    { source activate rapids || echo ok ; } && pip install -r requirements-system.txt

COPY python/requirements-app.txt ./
RUN --mount=type=cache,target=/root/.cache  \
    { source activate rapids || echo ok ; } && pip install -r requirements-app.txt

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN mkdir -p /root/.streamlit \
&& bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > /root/.streamlit/credentials.toml' \
&& bash -c 'echo -e "\
[server]\n\
enableXsrfProtection = false\n\ 
enableCORS = false\n\
[browser]\n\
gatherUsageStats = false\n\
" > /root/.streamlit/config.toml'

#Note no trailing slash
ENV BASE_URL=http://localhost:8501/dashboard
ENV BASE_PATH=dashboard/
ENV LOG_LEVEL=ERROR
COPY python/ /apps/

COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/apps/entrypoint.py"]

#Assume volume mount src/python as /apps/ (hot module reloading)