import graphistry, os, pandas as pd, streamlit as st
from time import sleep

from components import GraphistrySt, URLParam
from css import all_css

from util import getChild

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'app_01'
logger = getChild(app_id)
urlParams = URLParam(app_id)


def info():
    return {
        'id': app_id,
        'name': 'INTRO: fancy graph',
        'enabled': True,
        'tags': ['demo', 'demo_intro']
    }


def run():
    run_all()


############################################
#
#   CUSTOM CSS
#
############################################
# Have fun!

def custom_css():

    all_css()  # our favorites


############################################
#
#   SIDEBAR RENDER AERA
#
############################################
# Given URL params, render left sidebar form and return combined filter settings

# #https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area():
    st.sidebar.title('Pick graph')

    n_init = urlParams.get_field('N', 100)
    n = st.sidebar.number_input('Number of nodes', min_value=10, max_value=100000, value=n_init, step=20)
    urlParams.set_field('N', n)

    base_url = os.environ['BASE_URL']

    edges_df = pd.concat([
        pd.DataFrame({
            's': [x for x in range(n)],
            'd': [(x + 1) % n for x in range(n)],
            'link': [
                '<a href="' + base_url + '/?view_index=app1&app1_N=' + str(x % n) + '">' + str(x % n) + " nodes</a>"
                for x in range(n)
            ]
        }),
        pd.DataFrame({
            's': [x for x in range(n)],
            'd': [(x + 6) % n for x in range(n)],
            'link': [
                '<a href="' + base_url + '/?view_index=app1&app1_N=' + str(x % n) + '">' + str(x % n) + " nodes</a>"
                for x in range(n)
            ]
        })
    ], sort=False, ignore_index=True)

    st.sidebar.title("Filter")
    option_to_label = {
        'all': 'All',
        'odd': 'Odds',
        'even': 'Evens'
    }

    filter_by_node_type_init = urlParams.get_field('filter_by_type', default='all')
    filter_by_node_type = \
        st.sidebar.selectbox(
            'Filter nodes by:',
            ('all', 'odd', 'even'),
            index=('all', 'odd', 'even').index(filter_by_node_type_init),
            format_func=(lambda option: option_to_label[option]))
    urlParams.set_field('filter_by_type', filter_by_node_type)

    filter_by_node_range_init = (
        urlParams.get_field('filter_by_node_range_min', default=0),
        urlParams.get_field('filter_by_node_range_max', default=n))
    logger.info('filter_by_node_range_init: %s :: %s', filter_by_node_range_init, type(filter_by_node_range_init))
    filter_by_node_range = st.sidebar.slider(
        'Filter for nodes in range:',
        min_value=0, max_value=n, value=filter_by_node_range_init, step=1)
    urlParams.set_field('filter_by_node_range_min', filter_by_node_range[0])
    urlParams.set_field('filter_by_node_range_max', filter_by_node_range[1])

    return {
        'n': n,
        'edges_df': edges_df,
        'node_type': filter_by_node_type,
        'node_range': filter_by_node_range
    }


############################################
#
#   FILTER PIPELINE
#
############################################
# Given filter settings, generate/cache/return dataframes & viz

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters(node_type, node_range, edges_df, n):

    filtered_edges_df = edges_df
    if node_type == 'all':
        pass
    elif node_type == 'odd':
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] % 2 == 1 ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] % 2 == 1 ]
    elif node_type == 'even':
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] % 2 == 0 ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] % 2 == 0 ]
    else:
        raise Exception('Unknown filter1 option result: %s' % node_type)

    if node_range[0] > 0:
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] >= node_range[0] ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] >= node_range[0] ]
    if node_range[1] <= n:
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] <= node_range[1] ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] <= node_range[1] ]

    # include viz generation as part of cache
    url = plot_url(filtered_edges_df, n)

    return {
        'edges_df': filtered_edges_df,
        'url': url
    }


############################################
#
#   VIZ
#
############################################


def plot_url(edges_df, n):

    nodes_df = pd.DataFrame({
        'n': pd.concat([edges_df['s'], edges_df['d']]).unique()
    })

    nodes_df['nc'] = nodes_df['n'].apply(lambda v: 0x01000000 * round(255 * v / n))

    logger.info('Starting graphistry plot')
    if not GraphistrySt().test_login():
        return ''

    url = graphistry\
            .bind(source="s", destination="d")\
            .edges(edges_df)\
            .nodes(nodes_df)\
            .bind(node='n', point_color='nc')\
            .settings(url_params={
                'pointSize': 0.3,
                'splashAfter': 'false',
                'bg': '%23' + 'f0f2f6'
            })\
            .plot(render=False)

    logger.info('Generated viz, got back urL: %s', url)

    return url


############################################
#
#   MAIN RENDER AERA
#
############################################
# Given configured filters and computed results (cached), render

def main_area(edges_df, url):

    logger.debug('rendering main area, with url: %s', url)
    GraphistrySt().render_url(url)


############################################
#
#   Putting it all together
#
############################################

def run_all():

    custom_css()

    try:

        # Render sidebar and get current settings
        sidebar_filters = sidebar_area()

        logger.debug('sidebar_filters: %s', sidebar_filters)

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(**filter_pipeline_result)

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
