#!/bin/bash

#ex: --server.baseUrlPath="st_dashboard/" /apps/entrypoint.py

echo ""
echo ""
echo "                       _                                   _    _ _   "
echo "  __ _ _ __ __ _ _ __ | |__         __ _ _ __  _ __       | | _(_) |_ "
echo " / _\ | '__/ _\ | '_ \| '_ \ _____ / _\ | '_ \| '_ \ _____| |/ / | __|"
echo "| (_| | | | (_| | |_) | | | |_____| (_| | |_) | |_) |_____|   <| | |_ "
echo " \__, |_|  \__,_| .__/|_| |_|      \__,_| .__/| .__/      |_|\_\_|\__|"
echo " |___/          |_|                     |_|   |_|                     "
echo ""
echo ""
echo "Browser path (BASE_URL): $BASE_URL"
echo "StreamLit internal base path (BASE_PATH): $BASE_PATH"
echo "StreamLit host port (ST_PUBLIC_PORT): $ST_PUBLIC_PORT"
echo "StreamLit views mount host path (GRAPH_VIEW): $GRAPH_VIEW"
echo "Log level (LOG_LEVEL): $LOG_LEVEL"
echo "Graphistry user (GRAPHISTRY_USERNAME): $GRAPHISTRY_USERNAME"
echo ""

mkdir -p /root/.streamlit

if [[ -f "/root/gak/credentials.toml" ]]; then
    echo "Found custom credentials.toml, overriding default"
    cp /root/gak/credentials.toml /root/.streamlit/credentials.toml
fi


if [[ -f "/root/gak/config.toml" ]]; then
    echo "Found custom config.toml, overriding default"
    cp /root/gak/config.toml /root/.streamlit/config.toml
fi

# if ST_LOG_LEVEL is defined, set it for the base logger of the streamlit app by passing 
#  it in here. To set only set LOG_LEVEL for views and not the root logger for the app, 
#  use LOG_LEVEL

if [ -v ST_LOG_LEVEL ]; then
    PASS_LOG_LEVEL="--logger.level=${ST_LOG_LEVEL}"
fi

{ source activate rapids || echo ok ; } \
    && echo "pwd: `pwd`" && find . && streamlit run "$@" "${PASS_LOG_LEVEL}"
