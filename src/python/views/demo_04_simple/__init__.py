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


app_id = 'app_04'
logger = getChild(app_id)
urlParams = URLParam(app_id)


def info():
    return {
        'id': app_id,
        'name': 'INTRO: simple pipeline',
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
def sidebar_area():

    # regular param (not in url)
    e = st.sidebar.number_input('Number of edges', min_value=10, max_value=100000, value=100, step=20)

    # deep-linkable param (in url)
    n_init = urlParams.get_field('N', 100)
    n = st.sidebar.number_input('Number of nodes', min_value=10, max_value=100000, value=n_init, step=20)
    urlParams.set_field('N', n)

    return {'num_nodes': n, 'num_edges': e}


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters(num_nodes, num_edges):
    nodes_df = pd.DataFrame({ 'n': [x for x in range(0, num_nodes)] })
    edges_df = pd.DataFrame({
        's': [x % num_nodes for x in range(0, num_edges)],
        'd': [(x + 1) % num_nodes for x in range(0, num_edges)],
    })
    graph_url = \
        graphistry.nodes(nodes_df).edges(edges_df) \
            .bind(source='s', destination='d', node='n')\
            .plot(render=False)
    return { 'nodes_df': nodes_df, 'edges_df': edges_df, 'graph_url': graph_url }


def main_area(num_nodes, num_edges, nodes_df, edges_df, graph_url):
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

        # Render sidebar and get current settings
        sidebar_filters = sidebar_area()

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(**sidebar_filters, **filter_pipeline_result)

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
