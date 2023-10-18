import logging
import os
import random
import sys
from datetime import datetime, time
from typing import Any, Dict, List, Optional, Union

import dateutil.parser as dp
import numpy as np
import pandas as pd
from components import GraphistrySt, URLParam
from components.Splunk import SplunkConnection
from css import all_css
from graphistry.Plottable import Plottable

from views.demo_avr.marlowe import (
    AVR_SAFE_COLUMNS,
    FEATURE_COLUMNS,
    AVRDataResource,
    AVRMarlowe,
    AVRMissingData,
)

import streamlit as st

# App configuration
view_path = os.environ.get("VIEW_PATH", "/apps/views")
CSS_PATH = f"{view_path}/demo_avr/app.css"
DEFAULT_PIVOT_URL_INVESTIGATION_ID = "123"

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up

app_id = "demo_avr"
logger = logging.getLogger(app_id)
urlParams = URLParam(app_id)

INDEX: str = "avr_59k"
QUERY_SIZE = 5000


def info():
    return {
        "id": app_id,
        "name": "Cyber: Alert Explorer",
        "tags": ["demo", "demo_intro"],
        "enabled": True,
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

    with open(CSS_PATH, "r") as f:
        st.markdown(
            f"""<style>{f.read()}</style>""",
            unsafe_allow_html=True,
        )


# Given URL params, render left sidebar form and return combined filter settings
# https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area(cluster_id, general_probability, cluster_select_values):
    # Write a description in the sidebar
    st.sidebar.markdown(
        '<p style="font-size: 14px">Nodes: Alerts, colored by attack category</p>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<p style="font-size: 14px">Edges: Link alerts by similarity</p>',
        unsafe_allow_html=True,
    )

    st.sidebar.divider()

    # Use any query parameter for general_cluster to fill the selectbox
    pre_selected_index = 0
    try:
        pre_selected_index = cluster_select_values.index(str(cluster_id))
        logger.debug(
            f"We DID get a pre-selected-cluster ID. It's index is '{pre_selected_index}', its value is "
            + f"{cluster_select_values[pre_selected_index]}\n"
        )
    except ValueError as e:
        logger.error("URL cluster_id does not appear in sample :(")
        logger.exception(e)
        pre_selected_index = 0  # "None"

    start_date = st.sidebar.date_input("Start Date", value=datetime(2019, 3, 11))
    start_time = st.sidebar.time_input("Start Time", time(0, 00))
    end_date = st.sidebar.date_input("End Date", value=datetime(2019, 3, 18))
    end_time = st.sidebar.time_input("End Time", time(0, 00))

    logger.debug(f"start_date={start_date} start_time={start_time} end_date={end_date} end_time={end_time}\n")

    start_datetime = dp.parse(f"{start_date} {start_time}")
    end_datetime = dp.parse(f"{end_date} {end_time}")

    st.sidebar.divider()

    # # Create an advanced section of the menu you have to pop open
    # with st.expander("Advanced", expanded=True):

    # Get the cluster ID from the sidebar
    cluster_id: Optional[Union[str, int, List]] = st.sidebar.selectbox(
        label="Primary Correlation ID",
        options=cluster_select_values,
        index=pre_selected_index,
        key="cluster_id",
    )

    # Get the cluster confidence from the sidebar
    general_probability: Optional[float] = st.sidebar.slider(
        label="Minimum Cluster Probability",
        min_value=0.0,
        max_value=1.0,
        value=general_probability,
        step=0.1,
        key="general_probability",
    )

    # Query parameters from a shared URL
    query_params: Dict[str, Any] = st.experimental_get_query_params()

    # Finally, set any query params that have changed
    logger.debug(f"Almost final query_params: {query_params}\n")
    if cluster_id and (str(cluster_id) not in ("None", "")):
        query_params["cluster_id"] = [cluster_id]
    elif "cluster_id" in query_params:
        query_params.pop("cluster_id")

    if general_probability and (str(general_probability) not in ("None", "")):
        query_params["general_probability"] = [general_probability]
    elif "general_probability" in query_params:
        query_params.pop("general_probability")

    logger.debug(f"Final query_params: {query_params}\n")
    st.experimental_set_query_params(**query_params)

    return {
        "cluster_id": cluster_id,
        "general_probability": general_probability,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    }


# Given filter settings, generate/cache/return dataframes & viz
def run_filters(splunk_client, cluster_id, general_probability, start_datetime, end_datetime):
    query_dict: Dict[str, Union[str, float, List[str]]] = {
        "general_cluster": str(cluster_id),
        "general_probability": (">=", general_probability),
        "DetectTime": [(">=", start_datetime.isoformat()), ("<=", end_datetime.isoformat())],
    }

    filter_query = SplunkConnection.build_query(
        INDEX,
        query_dict=query_dict,
        fields=list(AVR_SAFE_COLUMNS.keys()),
    )
    logger.debug(f"filter_query: {filter_query}\n")

    # Get more data in the query than we sample down to ensure diversity
    with st.spinner("Retrieving data from Splunk ..."):
        splunk_edf: pd.DataFrame = splunk_client.one_shot_splunk(filter_query, count=QUERY_SIZE)

    data_resource: AVRDataResource = AVRDataResource(
        edf=splunk_edf,
        feature_columns=FEATURE_COLUMNS,
        debug=True,
    )

    investigation_id: str = os.getenv("PIVOT_URL_INVESTIGATION_ID", DEFAULT_PIVOT_URL_INVESTIGATION_ID)
    logger.debug(f"investigation_id={investigation_id}\n")

    #
    # Bring in standard graphistry environment variables: Set in .env --> docker-compose.yml --> os.getenv(key) --> AVRMarlowe.register()
    #

    logger.info("Configuring environment variables...\n")

    try:
        data_resource.trim_to_safe_cols(inplace=True)
        data_resource.clean_edge_list(inplace=True)
        data_resource.featurize_edges()
        data_resource.add_pivot_url_column(
            investigation_id=investigation_id,
        )
    except AVRMissingData as e:
        logger.error(f"Total records received from Splunk: {len(splunk_edf):,}\n")
        st.error("Your query returned no records.", icon="🚨")
        logger.exception(e, stack_info=True)

    # If we got data back...
    if len(data_resource.edf) > 0:
        with st.spinner("Generating graph..."):
            # Generate the graph
            marlowe: AVRMarlowe = AVRMarlowe(data_resource=data_resource)
            g: Plottable = marlowe.umap()
            graph_url: str = g.plot(render=False)

        # components.iframe(src=graph_url, height=HEIGHT, width=WIDTH, scrolling=True)
    else:
        st.error("Your query returned no records.", icon="🚨")

    return {"splunk_edf": splunk_edf, "graph_url": graph_url}


def main_area(splunk_edf, graph_url):
    logger.debug("rendering main area, with url: %s", graph_url)
    with st.spinner("Generating graph..."):
        GraphistrySt().render_url(graph_url)


############################################
#
#   PIPELINE FLOW
#
############################################


def run_all():
    custom_css()

    try:
        # Reproducible samples
        SEED = 31337
        random.seed = SEED
        np.random.seed = SEED

        splunk_username: str = os.getenv("SPLUNK_USERNAME")
        splunk_password: str = os.getenv("SPLUNK_PASSWORD")
        splunk_host: str = os.getenv("SPLUNK_HOST")
        logger.debug(f"splunk_username={splunk_username}, splunk_password={splunk_password}, splunk_host={splunk_host}\n")

        # if splunk host, username or password are not set, emit error and exit gracefully

        if splunk_username is None or splunk_password is None or splunk_host is None:
            logger.error("Missing required splunk host, username or password in environment variables, dashboard will not run.")
            st.write(" Error:  Missing required splunk host, username or password in environment variables, dashboard will not run without splunk configuration.")
        else:
            # Instantiate, connect and cache the Splunk client as a reusable resource
            splunk_client: Union[SplunkConnection, Any] = cache_splunk_client(splunk_username, splunk_password, splunk_host)

            # Query parameters from a shared URL
            query_params: Dict[str, Any] = st.experimental_get_query_params()

            # Log what we got
            logger.debug(f"Initial query_params: {query_params}\n")

            # Process the canonical cluster / incident ID and its probability - remove the list and get the value, deal with nulls
            cluster_id: Optional[Union[str, int]] = process_query_param("cluster_id", query_params.get("cluster_id"), query_params)
            general_probability: Optional[Union[str, float]] = process_query_param(
                "general_probability", query_params.get("general_probability"), query_params
            )

            # First we need to get all the unique
            with st.spinner("Retrieving cluster IDs from Splunk ..."):
                cluster_select_values = ["None"] + splunk_client.get_unique_values("avr_59k", "general_cluster")

            # Render sidebar and get current settings
            sidebar_params = sidebar_area(cluster_id, general_probability, cluster_select_values)

            # Compute filter pipeline (with auto-caching based on filter setting inputs)
            # Selective mark these as URL params as well
            filter_params = run_filters(splunk_client, **sidebar_params)

            # Render main viz area based on computed filter pipeline results and sidebar settings
            main_area(**filter_params)

    except Exception as exn:
        st.write("Error loading dashboard")
        st.write(exn)


#########################################################


# Cache the Splunk client as a resource so it is re-used
@st.cache_resource
def cache_splunk_client(username: str, password: str, host: str) -> SplunkConnection:
    splunk_client = SplunkConnection(username, password, host)
    assert splunk_client.connect()
    return splunk_client


def is_float_str(s: str) -> bool:
    """is_float_str Is it a float string?"""

    if s.replace(".", "", 1).isdigit() and (s.count(".") < 2):
        return True
    else:
        return False


# Process the canonical ID from query params - shouldn't a builtin utility do this?


def process_query_param(q_key: str, q_param: Optional[Union[str, int, float, List]], query_params: Dict[str, Any]):
    """process_query_param Get the canonical ID as an integer, if it exists."""
    clean_param: Optional[Union[str, int, float, List]] = None

    # Query parameters are lists, take the first item
    if isinstance(q_param, list):
        clean_param = q_param[0]

    # Did we get a clean version? Use it.
    if isinstance(clean_param, int):
        return clean_param
    if isinstance(clean_param, float):
        return clean_param

    # If the value was string "None", make it None, and remove from query parameters
    if isinstance(clean_param, str) and (clean_param == "None" or clean_param == ""):
        clean_param = None
        # We don't want ?cluster_id=None in a url, just delete ?cluster_id=
        if q_key in query_params:
            del query_params[q_key]
        return clean_param

    # Query parameters are strings, convert them to their numeric values
    if isinstance(clean_param, str):
        if clean_param.isdigit():
            clean_param = int(clean_param)
        elif is_float_str(clean_param):
            clean_param = float(clean_param)

    return clean_param


# Process the canonical ID from query params
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
