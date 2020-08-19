#!/bin/bash

source activate rapids && echo "pwd: `pwd`" && find . && streamlit run "$@"