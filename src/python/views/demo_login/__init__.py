import os
from datetime import datetime, time, timedelta
from typing import Dict, List, Union

import dateutil.parser as dp
from components import GraphistrySt, URLParam
from css import all_css
from graphistry import Plottable
from util import getChild
from views.demo_login.marlowe import (
    AUTH_SAFE_FIELDS,
    AuthDataResource,
    AuthMarlowe,
    AuthMissingData,
)
from views.demo_login.splunk import SplunkConnection

import streamlit as st

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = "demo_login"
logger = getChild(app_id)
urlParams = URLParam(app_id)

# Splunk configuration
INDEX = "auth_txt_50k"


def info():
    return {
        "id": app_id,
        "name": "Cyber: Auth Analysis",
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
    padding-top: 3.2rem;
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
    # regular param (not in url)
    # e = st.sidebar.number_input('Number of edges', min_value=10, max_value=100000, value=100, step=20)

    # deep-linkable param (in url)
    # n_init = urlParams.get_field('N', 100)
    # n = st.sidebar.number_input('Number of nodes', min_value=10, max_value=100000, value=n_init, step=20)
    # urlParams.set_field('N', n)

    with st.sidebar:
        today = datetime.now().date()
        current_hour = datetime.now().hour
        month_ago = today - timedelta(days=30)

        start_date = st.sidebar.date_input(label="Start Date", value=today)
        start_time = st.sidebar.time_input(label="Start Time", value=time(0, 00))
        end_date = st.sidebar.date_input(label="End Date", value=month_ago)
        end_time = st.sidebar.time_input(label="End Time", value=current_hour)

        logger.debug(f"start_date={start_date} start_time={start_time} | end_date={end_date} end_time={end_time}\n")

        start_datetime = dp.parse(f"{start_date} {start_time}")
        end_datetime = dp.parse(f"{end_date} {end_time}")

        st.sidebar.divider()

        urlParams.get_field("cluster_id", 1)
        cluster_id: int = st.sidebar.number_input(label="Cluster ID", value=1, step=1)
        urlParams.set_field("cluster_id", cluster_id)

        return {
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "cluster_id": cluster_id,
        }


# Cache the Splunk client as a resource so it is re-used
@st.cache_resource
def cache_splunk_client(username: str, password: str, host: str) -> SplunkConnection:
    splunk_client = SplunkConnection(username, password, host)
    assert splunk_client.connect()
    return splunk_client


# Given filter settings, generate/cache/return dataframes & viz
def run_filters(start_datetime, end_datetime, cluster_id):
    splunk_client = cache_splunk_client(
        os.environ["SPLUNK_USERNAME"],
        os.environ["SPLUNK_PASSWORD"],
        os.environ["SPLUNK_HOST"],
    )

    query_dict: Dict[str, Union[str, float, List[str]]] = {
        "dbscan": cluster_id,
        "datetime": [
            (">=", start_datetime.isoformat()),
            ("<=", end_datetime.isoformat()),
        ],
    }

    with st.spinner("Generating graph..."):
        results = splunk_client.one_shot_splunk(
            SplunkConnection.build_query(
                index=INDEX,
                query_dict=query_dict,
                fields=list(AUTH_SAFE_FIELDS.keys()),
                sort=[],
                debug=True,
            )
        )

        # Clean the Splunk results and send them to Graphistry to GPU render and return a url
        try:
            data_resource = AuthDataResource(edf=results, feature_columns=list(AUTH_SAFE_FIELDS.keys()))
            # Generate the graph
            marlowe: AuthMarlowe = AuthMarlowe(data_resource=data_resource)
            marlowe.register(
                api=3,
                protocol=os.getenv("GRAPHISTRY_PROTOCOL", "https"),
                server=os.getenv("GRAPHISTRY_SERVER", "hub.graphistry.com"),
                username=os.getenv("GRAPHISTRY_USERNAME"),
                password=os.getenv("GRAPHISTRY_PASSWORD"),
                client_protocol_hostname=os.getenv("GRAPHISTRY_CLIENT_PROTOCOL_HOSTNAME"),
            )
            g: Plottable = marlowe.umap()
            graph_url: str = g.plot(render=False)

            return {
                "graph_url": graph_url,
                "cluster_df": data_resource.cluster_df,
            }
        except AuthMissingData:
            st.error("Your query returned no records.", icon="🚨")


def main_area(
    start_datetime,
    end_datetime,
    cluster_id,
    graph_url=None,
    cluster_df=None,
):
    logger.debug("rendering main area, with url: %s", graph_url)
    GraphistrySt().render_url(graph_url)


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
