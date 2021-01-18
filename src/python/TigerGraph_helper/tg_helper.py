#Function to connect to TigerGraph

import os
import logging
import pyTigerGraphBeta as tg

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def connect_to_tigergraph():
    if ('TIGERGRAPH_HOST' in os.environ and 'TIGERGRAPH_USERNAME' in os.environ and 'TIGERGRAPH_PASSWORD' in os.environ and 'TIGERGRAPH_GRAPHNAME' in os.environ):
        host = os.environ["TIGERGRAPH_HOST"]
        username = os.environ["TIGERGRAPH_USERNAME"]
        password = os.environ["TIGERGRAPH_PASSWORD"]
        graphname = os.environ["TIGERGRAPH_GRAPHNAME"]
        conn = tg.TigerGraphConnection(host=host, graphname=graphname, username=username, password=password)
        if ('TIGERGRAPH_SECRET' in os.environ and os.environ["TIGERGRAPH_SECRET"] != None):
            secret = os.environ["TIGERGRAPH_SECRET"]
            conn.getToken(secret)
        else:
            conn.getToken(conn.createSecret())
        logger.info(host)
        return conn
    else:
        logging.error("Internal Configuraiton Error Occurred.  ")
        return None