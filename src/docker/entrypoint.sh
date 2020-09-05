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
echo ""

source activate rapids && echo "pwd: `pwd`" && find . && streamlit run "$@"