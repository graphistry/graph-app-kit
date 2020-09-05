import graphistry, os, pandas as pd, streamlit as st
from components import GraphistrySt, URLParam
from css import all_css
from util import getChild

### https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-gremlin-python.html
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

### Optional: local dev <> VPC [ ec2 proxy <> neptune instance ]
from sshtunnel import SSHTunnelForwarder

IS_LOCAL_DEV = True

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'app_neptune_01'
logger = getChild(app_id)
urlParams = URLParam(app_id)


def info():
    return {
        'id': app_id,
        'name': 'GREMLIN: sample',
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
        
        </style>""",unsafe_allow_html=True)


# Given URL params, render left sidebar form and return combined filter settings
#https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area():

    num_edges_init = urlParams.get_field('num_edges', 2000)
    num_edges = st.sidebar.slider('Number of edges', min_value=1, max_value=10000, value=num_edges_init, step=20)
    urlParams.set_field('num_edges', num_edges)


    return { 'num_edges': num_edges }


def plot_url(nodes_df, edges_df):

    logger.info('Starting graphistry plot')
    url = graphistry\
            .edges(edges_df)\
            .bind(source='s', destination='d', edge_label='l')\
            .nodes(nodes_df)\
            .bind(node='n', point_title='l')\
            .settings(url_params={
                'bg': '%23' + 'f0f2f6'
            })\
            .plot(render=False)

    logger.info('Generated viz, got back urL: %s', url)

    return url


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters(num_edges):

    graph = Graph()

    #See docker/.env & envs/neptune.env
    if not ('NEPTUNE_READER_HOST' in os.environ):
        raise RuntimeError('Demo requires NEPTUNE_READER_HOST (see envs/neptune.env)')

    cfg = {
        'NEPTUNE_READER_PROTOCOL': 'wss',
        'NEPTUNE_READER_HOST': None,
        'NEPTUNE_READER_PORT': 8182,
    }
    for k in cfg.keys():
        if k in os.environ:
            cfg[k] = os.environ[k]    

    NEPTUNE_READER_CONN_STR = cfg['NEPTUNE_READER_PROTOCOL'] + '://' + cfg['NEPTUNE_READER_HOST'] + ':' + str(cfg['NEPTUNE_READER_PORT']) + '/gremlin'
    logger.debug('Using neptune conn str: %s', NEPTUNE_READER_CONN_STR)

    server = None
    try:
        if 'NEPTUNE_TUNNEL_HOST' in os.environ:
            logger.debug('LOCAL_DEV')
            cfg = {
                **cfg,
                'NEPTUNE_TUNNEL_HOST': None,
                'NEPTUNE_TUNNEL_USER': 'ec2-user'
            }
            for k in cfg.keys():
                if k in os.environ:
                    cfg[k] = os.environ[k]
            logger.debug('Tunnel cfg: %s', cfg)

            logger.debug('disabling ssh context')            
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context

            logger.debug('configuring tunnel')            
            server = SSHTunnelForwarder(
                (cfg['NEPTUNE_TUNNEL_HOST'], 22),
                ssh_username=cfg['NEPTUNE_TUNNEL_USER'],
                ssh_pkey='/secrets/neptune-reader.pem',
                remote_bind_address=(cfg['NEPTUNE_READER_HOST'], int(cfg['NEPTUNE_READER_PORT'])),
                local_bind_address=('', 8182)
            )
            logger.debug('starting tunnel')            
            server.start()

            NEPTUNE_READER_CONN_STR= cfg['NEPTUNE_READER_PROTOCOL'] + '://localhost:' + str(server.local_bind_port) + '/gremlin'
            logger.debug('Tunneled neptune config: %s', NEPTUNE_READER_CONN_STR)

        remoteConn = DriverRemoteConnection(NEPTUNE_READER_CONN_STR, 'g')
        g = graph.traversal().withRemote(remoteConn)

        edges = g.E().limit(num_edges).toList()
        edges_df = pd.DataFrame([{'s': e.inV.id, 'd': e.outV.id, 'l': e.label} for e in edges])
        nodes = [e.inV for e in edges] + [e.outV for e in edges]
        nodes_df = pd.DataFrame([{'n': v.id, 'l': v.label} for v in nodes]).drop_duplicates(subset=['n']).reset_index(drop=True)

        url = plot_url(nodes_df, edges_df)

        try:
            remoteConn.close()
        except RuntimeError as e:
            st.warning(('Known error encountered when closing db conn', e))
        logger.debug('closed')

        return { 'nodes_df': nodes_df, 'edges_df': edges_df, 'url': url }
    except Exception as e:
        logger.error('oops in gremlin', exc_info=True)
        raise e
    finally:
        logger.debug("Cleaning up server if any: %s", not (server is None))
        if not (server is None):
            server.stop()
    
def main_area(num_edges, nodes_df, edges_df, url):

    logger.debug('rendering main area, with url: %s', url)
    GraphistrySt().render_url(url)

    st.write('nodes', nodes_df)
    st.write('edges', edges_df)



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

    
