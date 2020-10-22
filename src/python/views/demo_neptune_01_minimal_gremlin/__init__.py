import asyncio
import graphistry
import os
import pandas as pd
import streamlit as st
from components import GraphistrySt, URLParam
from css import all_css
from util import getChild
from neptune_helper import gremlin_helper, df_helper

from gremlin_python import statics
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import WithOptions, T

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'app_neptune_01'
logger = getChild(app_id)
urlParams = URLParam(app_id)
node_id_col = 'id'
src_id_col = 'source'
dst_id_col = 'target'
node_label_col = 'label'
edge_label_col = 'label'


def info():
    return {
        'id': app_id,
        'name': 'GREMLIN: Simple Sample',
        'tags': ['demo', 'neptune_demo']
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
def sidebar_area():

    num_edges_init = urlParams.get_field('num_edges', 100)
    num_edges = st.sidebar.slider(
        'Number of edges', min_value=1, max_value=10000, value=num_edges_init, step=20)
    urlParams.set_field('num_edges', num_edges)

    return {'num_edges': num_edges}


def plot_url(nodes_df, edges_df):
    nodes_df = df_helper.flatten_df(nodes_df)
    edges_df = df_helper.flatten_df(edges_df)

    logger.info('Starting graphistry plot')
    g = graphistry\
        .edges(edges_df)\
        .bind(source=src_id_col, destination=dst_id_col)\
        .nodes(nodes_df)\
        .bind(node=node_id_col)

    if not (node_label_col is None):
        g = g.bind(point_title=node_label_col)

    if not (edge_label_col is None):
        g = g.bind(edge_title=edge_label_col)

    url = g\
        .settings(url_params={
            'bg': '%23' + 'f0f2f6'
        })\
        .plot(render=False)

    logger.info('Generated viz, got back urL: %s', url)

    return url


def path_to_df(p):
    nodes = {}
    edges = {}

    for triple in p:

        src_id = triple[0][T.id]
        nodes[src_id] = df_helper.vertex_to_dict(triple[0])

        dst_id = triple[2][T.id]
        nodes[dst_id] = df_helper.vertex_to_dict(triple[2])

        edges[triple[1][T.id]] = df_helper.edge_to_dict(
            triple[1], src_id, dst_id)

    return pd.DataFrame(nodes.values()), pd.DataFrame(edges.values())


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters(num_edges):
    g, conn = gremlin_helper.connect_to_neptune()

    logger.info('Querying neptune')
    res = g.V().inE().limit(num_edges).outV().path().by(
        __.valueMap().with_(WithOptions.tokens)).toList()

    nodes_df, edges_df = path_to_df(res)
    url = plot_url(nodes_df, edges_df)

    logger.info("Finished compute phase")

    try:
        conn.close()

    except RuntimeError as e:
        if str(e) == "There is no current event loop in thread 'ScriptRunner.scriptThread'.":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            conn.close()
        else:
            raise e

    except Exception as e:
        logger.error('oops in gremlin', exc_info=True)
        raise e

    return {'nodes_df': nodes_df, 'edges_df': edges_df, 'url': url, 'res': res}


def main_area(url):

    logger.debug('rendering main area, with url: %s', url)
    GraphistrySt().render_url(url)


############################################
#
#   PIPELINE FLOW
#
############################################


def run_all():
    try:
        custom_css()

        # Render sidebar and get current settings
        sidebar_filters = sidebar_area()

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(filter_pipeline_result['url'])

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
