#!/bin/bash

#ex: --server.baseUrlPath="st_dashboard/" /apps/entrypoint.py
source activate rapids && echo "pwd: `pwd`" && find . && streamlit run "$@"