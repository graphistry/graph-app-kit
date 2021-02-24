import logging, os, pyTigerGraphBeta as tg
from typing import Optional
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


TIGERGRAPH_CONNECTION_VERSION = '3.1.0'


def connect_to_tigergraph() -> Optional[dict]:
    if ('TIGERGRAPH_HOST' in os.environ and 'TIGERGRAPH_USERNAME' in os.environ
        and 'TIGERGRAPH_PASSWORD' in os.environ and 'TIGERGRAPH_GRAPHNAME' in os.environ):

        creds = {
            'host': os.environ["TIGERGRAPH_HOST"],
            'username': os.environ["TIGERGRAPH_USERNAME"],
            'password': os.environ["TIGERGRAPH_PASSWORD"],
            'graphname': os.environ["TIGERGRAPH_GRAPHNAME"]
        }
        logger.info('Connecting to TigerGraph using environment variables: %s',
            {**creds,
            'password': ''.join(['*' for x in creds['password']]) if creds['password'] is not None else ''})

        conn = tg.TigerGraphConnection(**creds, version=TIGERGRAPH_CONNECTION_VERSION)

        if ('TIGERGRAPH_SECRET' in os.environ and os.environ["TIGERGRAPH_SECRET"] is not None):
            logger.info('... Connected to TG, getting token via provided secret...')
            secret = os.environ["TIGERGRAPH_SECRET"]
            conn.getToken(secret)
        else:
            # FIXME: This times out in practice, maybe TG 3.0 -> 3.1 version issues?
            logger.info('... Connected to TG, creating secret and getting token...')
            conn.getToken(conn.createSecret())

        logger.info('Successfully finished connecting to TG!')
        return conn

    logger.debug("Missing TigerGraph environment variables; skipping connection")
    return None
