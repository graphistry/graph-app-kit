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

rm -f /root/.streamlit/credentials.toml
cp /root/gak/credentials.toml /root/.streamlit/credentials.toml


rm -f /root/.streamlit/config.toml
cp /root/gak/config.toml /root/.streamlit/config.toml

echo -e "\
    baseUrlPath = \"$BASE_PATH\"\n\
    " >> /root/.streamlit/config.toml


#&& ( \
#    cd /apps/views/DT \
#    && GRAPHISTRY_USERNAME=leotest2 GRAPHISTRY_PASSWORD=accountaccount \
#    python3 -m text_utils.pipeline -n pfas -i 0 -s 0 \
#) \

{ source activate rapids || echo ok ; } \
    && echo "pwd: `pwd`" && find . && streamlit run "$@"