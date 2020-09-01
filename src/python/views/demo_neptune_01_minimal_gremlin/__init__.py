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
        'name': 'app6: neptune'
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

    return { }


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters():

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

        logger.debug(('out', g.V().limit(2).toList()))
        remoteConn.close()

        return { }
    except Exception as e:
        logger.error('oops in gremlin', exc_info=True)
        raise e
    finally:
        logger.debug("Cleaning up server if any: %s", not (server is None))
        if not (server is None):
            server.stop()
    
def main_area():
    pass


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

    
