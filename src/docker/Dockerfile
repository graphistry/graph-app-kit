ARG APP_BUILD_TAG=latest
ARG VERSION_BASE=v2.31.5
FROM graphistry/graphistry-forge-base:${VERSION_BASE}

# exposing default port for streamlit
EXPOSE 8501

# making directory of app
WORKDIR /app

# copy over requirements
COPY python/requirements-app.txt python/requirements-system.txt ./

# TODO system/user conda environment.yml before pip
RUN source activate rapids \
    && pip install streamlit==0.65.2 \
    && pip install -r requirements-system.txt

RUN pip install -r requirements-app.txt

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
" > /root/.streamlit/config.toml'

COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/apps/entrypoint.py"]

#Assume volume mount src/python as /apps/ (hot module reloading)