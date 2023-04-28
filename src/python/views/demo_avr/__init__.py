import logging
import os
import random
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd
import streamlit as st

from natsort import natsorted
from numbers import Number
from streamlit.components import v1 as components
from streamlit.logger import get_logger
from typeguard import typechecked

# from avr_helper.marlowe import AVRMarlowe
# from avr_helper.splunk import SplunkConnection
from views.demo_avr.marlowe import AVRMarlowe
from views.demo_avr.splunk import SplunkConnection

#############################################
# demo simple code: 

import graphistry, pandas as pd, streamlit as st
from components import GraphistrySt, URLParam
from css import all_css
from util import getChild

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'demo_avr'
logger = getChild(app_id)
urlParams = URLParam(app_id)


def info():
    return {
        'id': app_id,
        'name': 'Incident Group Explorer',
        'tags': ['demo', 'demo_intro']
    }


def run():
    run_all()


############################################
#
#   PIPELINE PIECES
#
############################################


# Have fun!
def custom_css():
    all_css()
    st.markdown(
        """<style>

        </style>""", unsafe_allow_html=True)


# Given URL params, render left sidebar form and return combined filter settings
# https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area(clusters):

    # Get the query params for all our widget initial values
    query_params = st.experimental_get_query_params()

    # Get the cluster ID from the sidebar
    cluster_id = st.sidebar.selectbox(
        "Primary Correlation ID",
        clusters,
        key="cluster_id",
    )

    if cluster_id and isinstance(cluster_id, str) and cluster_id not in ("", "None"):
        cluster_id = int(cluster_id)

    with st.sidebar.expander("Advanced"):
        # Get the cluster confidence from the sidebar
        general_probability = st.sidebar.slider(
            "Minimum Cluster Probability", 0.0, 1.0, 0.0, 0.1, key="general_probability"
        )

        st.sidebar.button("Refresh")

    # Finally, set any query params that have changed
    if cluster_id and (cluster_id is not None) and (cluster_id not in ("None", "")):
        query_params["cluster_id"] = [cluster_id]

    st.experimental_set_query_params(**query_params)

    return

# Given filter settings, generate/cache/return dataframes & viz
#@st.cache(suppress_st_warning=True, allow_output_mutation=True)
@st.cache_data
def run_filters(splunk_edf): 
    
    graphistry_username: str = os.getenv("GRAPHISTRY_USERNAME")
    graphistry_password: str = os.getenv("GRAPHISTRY_PASSWORD")
    graphistry_protocol: str = os.getenv("GRAPHISTRY_PROTOCOL")
    graphistry_host: str = os.getenv("GRAPHISTRY_HOSTNAME")
    #print(graphistry_username, graphistry_password, graphistry_protocol, graphistry_host)

    # Get the query params for all our widget initial values
    query_params = st.experimental_get_query_params()

    cluster_id = query_params.get("cluster_id")
    general_probability = query_params.get("general_probability")    

    if cluster_id and isinstance(cluster_id, int):
        splunk_edf = splunk_edf[splunk_edf["general_cluster"] == cluster_id]
        assert len(splunk_edf > 0)

    if general_probability and isinstance(general_probability, Number):
        splunk_edf = splunk_edf[splunk_edf["general_probability"] > general_probability]

    with st.spinner("Generating graph..."):
        # 0 is a valid cluster ID
        if (cluster_id != 0) and (not cluster_id) or (cluster_id in ("None", "")):
            # We don't have a filter - sample
            splunk_edf = splunk_edf.sample(n=1000) if len(splunk_edf.index) > 1000 else splunk_edf
        # We do have a filter - make sure the data isn't excessive
        else:
            max_edf = min(len(splunk_edf.index), 1000)
            splunk_edf = splunk_edf[:max_edf]

        # Generate the graph
        marlowe = AVRMarlowe(edf=splunk_edf)
        # not needed: 
        # marlowe.register(
        #     api=3,
        #     username=graphistry_username,
        #     protocol=graphistry_protocol,
        #     password=graphistry_password,
        #     host=graphistry_host,
        #     client_protocol_hostname="heracles",
        #     debug=True,
        # )
        graph_url = marlowe.umap(render=False)


    return graph_url

def main_area(graph_url): 
    logger.debug('rendering main area, with url: %s', graph_url)
    GraphistrySt().render_url(graph_url)
    

############################################
#
#   PIPELINE FLOW
#
############################################


def run_all():

    custom_css()

    try:

        # Logging is too much! Quiet it down.
        logger = get_logger(__name__)
        logger.setLevel(logging.WARNING)

        HEIGHT = 800
        WIDTH = 1300

        # Reproducible samples
        SEED = 31337
        random.seed = SEED
        np.random.seed = SEED

        splunk_username: str = os.getenv("SPLUNK_USERNAME")
        splunk_password: str = os.getenv("SPLUNK_PASSWORD")
        splunk_host: str = os.getenv("SPLUNK_HOST")
        print(splunk_username, splunk_password, splunk_host)

        AVR_SAFE_COLUMNS: Dict[str, Any] = {
            "DetectTime": "datetime",
            "Category": str,
            "ID": str,
            "Node_SW": str,
            "Node_Type": str,
            "Node_Name": str,
            "Source_Port": str,
            "Source_IP4": str,
            "Source_Proto": str,
            "Target_Port": str,
            "Target_IP4": str,
            "Target_Proto": str,
            "Source_IP4_Subnet_16": str,
            "Source_IP4_Subnet_24": str,
            "Target_IP4_Subnet_16": str,
            "Target_IP4_Subnet_24": str,
            "x": float,
            "y": float,
            "general_cluster": int,
            "general_probability": float,
            "specific_cluster": int,
            "specific_probability": float,
        }

        st.markdown(
            """
                <style>
                    .block-container {
                        padding-top: 1rem;
                        padding-bottom: 0rem;
                        padding-left: 5rem;
                        padding-right: 5rem;
                    }
                    .main { align-items: left; }
                    .block-container {
                        padding-left: 2rem;
                        padding-right: 2rem;
                    }
                    header { display: none !important; }
                    footer { display: none !important; }
                </style>
                """,
            unsafe_allow_html=True,
        )

        # st.header(TITLE)

        # Get the query params for all our widget initial values
        query_params = st.experimental_get_query_params()

        # Process the canonical cluster / incident ID
        cluster_id: Union[None, str, int] = preprocess_cluster_id(
            query_params.get("cluster_id"), query_params
        )

        # Get the Splunk data, extract cluster IDs for the select box
        splunk_client: SplunkConnection = cache_splunk_client(
            splunk_username, splunk_password, splunk_host
        )
        query_field_str: str = " ".join(AVR_SAFE_COLUMNS)
        query: str = f'search index="avr_59k" | fields {query_field_str}'
        splunk_edf: pd.DataFrame = splunk_client.one_shot_splunk(query, count=1000)

        # Drop unnecessary fields
        splunk_edf = splunk_edf.drop(
            columns=[
                "_bkt",
                "_cd",
                "_raw",
                "_time",
            ],
            axis=1,
        )

        clusters: List[str] = ["None"] + natsorted(
            # Cluster -1 is a random noise
            splunk_edf["general_cluster"]
            .fillna(-1)
            .drop_duplicates()
            .astype(str)
            .tolist()
        )

        # Render sidebar and get current settings
        sidebar_area(clusters)

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        graph_url = run_filters(splunk_edf) 

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(graph_url) 

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)



#########################################################


def clean_edge_list(edf: pd.DataFrame, debug=False) -> pd.DataFrame:
    """clean_edge_list Clean up the edges by casting them."""
    edf = edf[AVR_SAFE_COLUMNS.keys()]

    for col, cast in AVR_SAFE_COLUMNS.items():
        logger.warning(f"Column: {col} Cast: {cast}") if debug else None
        edf[col] = pd.to_datetime(edf[col]) if cast == "datetime" else edf[col].astype(cast)

    return edf


@st.cache_resource
def cache_splunk_client(username: str, password: str, host: str) -> SplunkConnection:
    splunk_client: SplunkConnection = SplunkConnection(username, password, host)
    return splunk_client


# Process the canonical ID from query params
@typechecked
def preprocess_cluster_id(cluster_id: Union[None, str, int, List], query_params: Dict[str, Any]):
    """Get the canonical ID as an integer, if it exists."""
    # Query parameters are lists, take the first item
    if isinstance(cluster_id, list):
        cluster_id = cluster_id[0]
    # If the value was string "None", make it None, remove from query parameters
    if isinstance(cluster_id, str) and cluster_id == "None":
        cluster_id = None
        del query_params["cluster_id"]
    # Query parameters are strings, make it an integer
    if isinstance(cluster_id, str):
        cluster_id = int(cluster_id)
    return cluster_id
