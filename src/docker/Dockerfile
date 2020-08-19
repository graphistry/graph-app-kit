ARG APP_BUILD_TAG=latest
ARG VERSION_BASE=latest
FROM graphistry/graphistry-forge-base:${VERSION_BASE}

# exposing default port for streamlit
EXPOSE 8501

# making directory of app
WORKDIR /app

# copy over requirements
COPY requirements.txt ./requirements.txt

# install pip then packages
RUN source activate rapids \
    && pip install streamlit==0.65.2 \
    && pip install -r requirements.txt

# cmd to launch app when container is run
#CMD streamlit run app.py
#CMD [ "streamlit", "run", "webapp/app.py" ]
#CMD /bin/bash

# streamlit-specific commands for config
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN mkdir -p /root/.streamlit
RUN bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > /root/.streamlit/credentials.toml'

RUN bash -c 'echo -e "\
[server]\n\
enableXsrfProtection = false\n\ 
enableCORS = false\n\
" > /root/.streamlit/config.toml'

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/apps/entrypoint.py"]

# volume mount src/ as /apps/, assumes /apps/entrypoint.py
# COPY . /app
