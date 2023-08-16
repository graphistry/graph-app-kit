import logging
import os
import sys
from datetime import datetime, time, timedelta
from typing import Dict, List, Union

import dateutil.parser as dp
import pandas as pd
import streamlit.components.v1 as components
from components import URLParam
from components.Splunk import SplunkConnection
from css import all_css
from graphistry import Plottable
from requests.exceptions import HTTPError
from views.demo_login.marlowe import (
    AUTH_SAFE_FIELDS,
    AuthDataResource,
    AuthMarlowe,
    AuthMissingData,
)

import streamlit as st

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = "demo_login"
logger = logging.getLogger(app_id)
urlParams = URLParam(app_id)

# Splunk configuration
INDEX = "auth_txt_50k"
DEFAULT_PIVOT_URL_INVESTIGATION_ID = "123"


def info():
    return {
        "id": app_id,
        "name": "Cyber: Login Analyzer",
        "tags": ["cyber", "cybersecurity", "security"],
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
    st.markdown(
        """<style>
.block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

.main {
    align-items: left;
}

h2 {
    padding-top: 0rem;
    padding-bottom: 0.5rem;
}

[data-testid="stSidebar"] {
    width: 300px !important;
}

.e1fqkh3o4 {
    padding-top: 1.2rem;
    padding-bottom: 0rem;
    padding-left: 0rem;
    padding-right: 0rem;
}

/* Hide the Built with streamlit header/footer */
header {
    display: none !important;
}

footer {
    display: none !important;
}

hr {
    margin-block-start: 0.1rem;
    margin-block-end: 0.1rem;
}
</style>""",
        unsafe_allow_html=True,
    )


# Given URL params, render left sidebar form and return combined filter settings
# https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area():
    with st.sidebar:
        # Write a description in the sidebar
        st.sidebar.markdown(
            '<p style="font-size: 14px">Nodes: Logins, colored by attack category</p>',
            unsafe_allow_html=True,
        )
        st.sidebar.markdown(
            '<p style="font-size: 14px">Edges: Link logins by similarity</p>',
            unsafe_allow_html=True,
        )

        st.sidebar.divider()

        now = datetime.now()
        today = now.date()
        current_hour = now.time()
        month_ago = today - timedelta(days=60)

        start_date = st.sidebar.date_input(label="Start Date", value=month_ago)
        start_time = st.sidebar.time_input(label="Start Time", value=time(0, 00))
        end_date = st.sidebar.date_input(label="End Date", value=now)
        end_time = st.sidebar.time_input(label="End Time", value=current_hour)

        logger.debug(f"start_date={start_date} start_time={start_time} | end_date={end_date} end_time={end_time}\n")

        start_datetime = dp.parse(f"{start_date} {start_time}")
        end_datetime = dp.parse(f"{end_date} {end_time}")

        # st.sidebar.divider()

        # urlParams.get_field("dbscan", 0)
        # dbscan: int = st.sidebar.number_input(label="Cluster ID", value=0, step=1)
        # urlParams.set_field("dbscan", dbscan)

        return {
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            # "dbscan": dbscan,
        }


# Cache the Splunk client as a resource so it is re-used
@st.cache_resource
def cache_splunk_client(username: str, password: str, host: str) -> SplunkConnection:
    splunk_client = SplunkConnection(username, password, host)
    assert splunk_client.connect()
    return splunk_client


# Given filter settings, generate/cache/return dataframes & viz
def run_filters(start_datetime, end_datetime):  # , dbscan):
    with st.spinner("Generating graph..."):
        splunk_client = cache_splunk_client(
            os.environ["SPLUNK_USERNAME"],
            os.environ["SPLUNK_PASSWORD"],
            os.environ["SPLUNK_HOST"],
        )

        query_dict: Dict[str, Union[str, float, List[str]]] = {
            "datetime": [
                (">=", start_datetime.isoformat()),
                ("<=", end_datetime.isoformat()),
            ],
        }
        # if dbscan > 0:
        #     query_dict["dbscan"] = dbscan

        splunk_query = SplunkConnection.build_query(
            index=INDEX,
            query_dict=query_dict,
            fields=list(AUTH_SAFE_FIELDS.keys()),
            sort=[],
            debug=True,
        )
        logger.debug(f"Splunk query: {splunk_query}\n")
        results = splunk_client.one_shot_splunk(splunk_query)

        # Clean the Splunk results and send them to Graphistry to GPU render and return a url
        try:
            data_resource = AuthDataResource(edf=results, feature_columns=list(AUTH_SAFE_FIELDS.keys()))

            #
            # Bring in standard graphistry environment variables: Set env/*.env files, in .env --> docker-compose.yml --> os.getenv(key) --> AVRMarlowe.register()
            #

            logger.info("Configuring environment variables...\n")
            investigation_id: str = os.getenv("PIVOT_URL_INVESTIGATION_ID", DEFAULT_PIVOT_URL_INVESTIGATION_ID)
            logger.debug(f"investigation_id={investigation_id}\n")

            data_resource.add_pivot_url_column(
                investigation_id=investigation_id,
            )

            # Generate the graph
            marlowe: AuthMarlowe = AuthMarlowe(data_resource=data_resource)
            g: Plottable = marlowe.umap()  # next line describe_clusters uses dbscan clusters from umap
            cluster_df: pd.DataFrame = marlowe.describe_clusters()
            try:
                graph_url: str = g.plot(render=False)
            except HTTPError as e:
                logging.exception(e)

            return {
                "graph_url": graph_url,
                "cluster_df": cluster_df,
            }
        except AuthMissingData:
            st.error("Your query returned no records.", icon="🚨")


def main_area(
    start_datetime,
    end_datetime,
    # dbscan,
    graph_url=None,
    cluster_df=None,
):
    logger.debug("Rendering main area, with url: %s\n", graph_url)
    components.iframe(src=graph_url, height=650, scrolling=True)
    st.dataframe(cluster_df, use_container_width=True, height=176)


############################################
#
#   PIPELINE FLOW
#
############################################


def run_all():
    custom_css()

    try:
        # Render sidebar and get current settings
        sidebar_filters = sidebar_area()

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(
            **sidebar_filters,
            # Fill in empties or main_area will choke
            **filter_pipeline_result or {"graph_url": None, "cluster_df": None},
        )

    except Exception as exn:
        st.write("Error loading dashboard")
        st.write(exn)
