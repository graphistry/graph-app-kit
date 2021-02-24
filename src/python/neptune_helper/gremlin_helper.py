import os
import logging
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.strategies import *
from gremlin_python.process.traversal import *
from gremlin_python.structure.graph import Path, Vertex, Edge
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def connect_to_neptune():
    """Creates a connection to Neptune and returns the traversal source"""
    if ('NEPTUNE_READER_HOST' in os.environ and 'NEPTUNE_READER_PORT' in os.environ
            and 'NEPTUNE_READER_PROTOCOL' in os.environ):
        server = os.environ["NEPTUNE_READER_HOST"]
        port = os.environ["NEPTUNE_READER_PORT"]
        protocol = os.environ["NEPTUNE_READER_PROTOCOL"]
        endpoint = f'{protocol}://{server}:{port}/gremlin'
        logger.info(endpoint)
        connection = DriverRemoteConnection(endpoint, 'g')
        gts = traversal().withRemote(connection)
        return (gts, connection)
    else:
        logging.error("Internal Configuraiton Error Occurred.  ")
        return None
