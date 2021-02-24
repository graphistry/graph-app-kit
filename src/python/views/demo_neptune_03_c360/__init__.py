import asyncio
import graphistry
import os
import pandas as pd
import streamlit as st
from components import GraphistrySt, URLParam
from neptune_helper import gremlin_helper, df_helper
from css import all_css
from util import getChild
import time
import altair as alt

from gremlin_python import statics
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import WithOptions, T, TextP

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'app_neptune_03'
logger = getChild(app_id)
urlParams = URLParam(app_id)
node_id_col = 'id'
src_id_col = 'source'
dst_id_col = 'target'
node_label_col = 'label'
edge_label_col = 'label'

# Setup a structure to hold metrics
metrics = {'neptune_time': 0, 'graphistry_time': 0,
           'node_cnt': 0, 'edge_cnt': 0, 'prop_cnt': 0}


# Define the name of the view
def info():
    return {
        'id': app_id,
        'name': 'GREMLIN: Customer 360',
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

    num_edges_init = urlParams.get_field('num_edges', 10000)

    transient_id = st.sidebar.text_input(
        'Show me items starting with this transient id?',
        "")

    num_matches = st.sidebar.slider(
        'Number of matches', min_value=1, max_value=100, value=50, step=5)

    num_edges = st.sidebar.slider(
        'Number of edges', min_value=1, max_value=10000, value=num_edges_init, step=20)
    urlParams.set_field('num_edges', num_edges)

    return {'num_edges': num_edges, 'num_matches': num_matches, 'transient_id': transient_id}


def plot_url(nodes_df, edges_df):
    global metrics
    nodes_df = df_helper.flatten_df(nodes_df)
    edges_df = df_helper.flatten_df(edges_df)

    logger.info('Starting graphistry plot')
    tic = time.perf_counter()
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
    toc = time.perf_counter()
    metrics['graphistry_time'] = toc - tic
    logger.info(f'Graphisty Time: {metrics["graphistry_time"]}')
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
def run_filters(num_edges, num_matches, transient_id):
    global metrics
    g, conn = gremlin_helper.connect_to_neptune()

    logger.info('Querying neptune')
    tic = time.perf_counter()
    t = g.V().hasLabel('transientId')
    if not transient_id == "":
        # If using Neptune full text search this will perform much faster than the built in Gremlin text search
        t = t.has('uid', TextP.containing(transient_id))
    res = t.limit(num_matches).bothE().otherV().limit(num_edges).path().by(
        __.valueMap().with_(WithOptions.tokens)).toList()

    toc = time.perf_counter()
    logger.info(f'Query Execution: {toc-tic:0.02f} seconds')
    logger.debug('Query Result Count: %s', len(res))
    metrics['neptune_time'] = toc - tic

    nodes_df, edges_df = path_to_df(res)

    # Calculate the metrics
    metrics['node_cnt'] = nodes_df.size
    metrics['edge_cnt'] = edges_df.size
    metrics['prop_cnt'] = (nodes_df.size * nodes_df.columns.size) + \
        (edges_df.size * edges_df.columns.size)

    if nodes_df.size > 0:
        url = plot_url(nodes_df, edges_df)
    else:
        url = ""

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


def main_area(url, nodes, edges):

    logger.debug('rendering main area, with url: %s', url)
    GraphistrySt().render_url(url)


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

        # Render main viz area based on computed filter pipeline results and sidebar settings if data is returned
        if filter_pipeline_result['nodes_df'].size > 0:
            main_area(filter_pipeline_result['url'],
                      filter_pipeline_result['nodes_df'],
                      filter_pipeline_result['edges_df'])
        else:  # render a message
            st.write("No data matching the specfiied criteria is found")

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
