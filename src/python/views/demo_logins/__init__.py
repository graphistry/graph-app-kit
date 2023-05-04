import os
from datetime import datetime, time
from typing import Dict, List, Union

import dateutil.parser as dp
import pandas as pd
from components import GraphistrySt, URLParam
from css import all_css
from graphistry import Plottable
from util import getChild
from views.demo_logins.marlowe import AUTH_SAFE_FIELDS, AVRDataResource, AVRMarlowe, AVRMissingData
from views.demo_logins.splunk import SplunkConnection

import streamlit as st

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = "auth_analysis"
logger = getChild(app_id)
urlParams = URLParam(app_id)

# Splunk configuration
INDEX = "auth_txt_50k"


def info():
    return {
        "id": app_id,
        "name": "Auth Analysis",
        "tags": ["prod", "demo", "cyber", "cybersecurity", "security"],
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
        start_date = st.sidebar.date_input("Start Date", value=datetime(2019, 3, 11))
        start_time = st.sidebar.time_input("Start Time", time(0, 00))
        end_date = st.sidebar.date_input("End Date", value=datetime(2019, 3, 18))
        end_time = st.sidebar.time_input("End Time", time(0, 00))

        logger.debug(
            f"start_date={start_date} start_time={start_time} end_date={end_date} end_time={end_time}\n"
        )

        start_datetime = dp.parse(f"{start_date} {start_time}")
        end_datetime = dp.parse(f"{end_date} {end_time}")

        st.sidebar.divider()

        cluster_id: int = st.sidebar.number_input("Cluster ID", value=0, step=1)

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


def make_cluster_df(ndf: pd.DataFrame, cluster_id: int) -> pd.DataFrame:
    cluster_df = ndf[ndf["_dbscan"] == cluster_id]


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(
    suppress_st_warning=True,
    allow_output_mutation=True,
    hash_funcs={pd.DataFrame: lambda _: None},
)
def run_filters(start_datetime, end_datetime, cluster_id):
    splunk_client = cache_splunk_client(
        os.environ["SPLUNK_USERNAME"],
        os.environ["SPLUNK_PASSWORD"],
        os.environ["SPLUNK_HOST"],
    )

    query_dict: Dict[str, Union[str, float, List[str]]] = {
        "_dbscan": cluster_id,
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
            )
        )

        try:
            dr = AVRDataResource(edf=results, feature_columns=list(AUTH_SAFE_FIELDS.keys()))
            marlowe = AVRMarlowe(data_resource=dr)
        except AVRMissingData:


        # Generate the graph
        marlowe: AVRMarlowe = AVRMarlowe(data_resource=dr)
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

        cluster_df: pd.DataFrame = make_cluster_df(g._nodes, cluster_id)

        return {
            "graph_url": graph_url,
            "cluster_df": cluster_df,
        }


def main_area(
    num_nodes, num_edges, bank, bank_ids, nodes_df, edges_df, graph_url, ego_banks_df
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
        main_area(**sidebar_filters, **filter_pipeline_result)

    except Exception as exn:
        st.write("Error loading dashboard")
        st.write(exn)
