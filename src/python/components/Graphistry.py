import graphistry, os, streamlit as st
from graphistry import PyGraphistry

from util import getChild
logger = getChild(__name__)

logger.debug('Using graphistry version: %s', graphistry.__version__)


class GraphistrySt:

    def __init__(self, overrides={}):
        cfg = {
            'api': 3,
            **({'username': os.environ['GRAPHISTRY_USERNAME']} if 'GRAPHISTRY_USERNAME' in os.environ else {}),
            **({'password': os.environ['GRAPHISTRY_PASSWORD']} if 'GRAPHISTRY_PASSWORD' in os.environ else {}),
            **({'token': os.environ['GRAPHISTRY_TOKEN']} if 'GRAPHISTRY_TOKEN' in os.environ else {}),
            **({'protocol': os.environ['GRAPHISTRY_PROTOCOL']} if 'GRAPHISTRY_PROTOCOL' in os.environ else {}),
            **({'server': os.environ['GRAPHISTRY_SERVER']} if 'GRAPHISTRY_SERVER' in os.environ else {}),
            **({'client_protocol_hostname': os.environ['GRAPHISTRY_CLIENT_PROTOCOL_HOSTNAME']}
                if 'GRAPHISTRY_CLIENT_PROTOCOL_HOSTNAME' in os.environ
                else {}),
            **overrides
        }
        if not (('username' in cfg) and ('password' in cfg)) and not ('token' in cfg):
            logger.info('No graphistry creds set, skipping')
            return
        if not ('store_token_creds_in_memory' in cfg):
            cfg['store_token_creds_in_memory'] = True
        graphistry.register(**cfg)
        graphistry.login(username=cfg['username'], password=cfg['password'])

    def render_url(self, url):
        if self.test_login():
            logger.debug('rendering main area, with url: %s', url)
            iframe = '<iframe src="' + url + '", height="800", width="100%" allow="fullscreen"></iframe>'
            st.markdown(iframe, unsafe_allow_html=True)

    def plot(self, g):
        if PyGraphistry._is_authenticated:
            url = g.plot(as_files=True, render=False)  # TODO: Remove as_files=True when becomes default
            self.render_url(url)
        else:

            st.markdown("""
                Graphistry not authenticated. Did you set credentials in docker/.env based on envs/graphistry.env ?
            """)

    def test_login(self, verbose=True):
        try:
            graphistry.register()
            return True
        except:  # noqa: E722
            if verbose:
                st.write(Exception("""Not logged in for Graphistry plots:
                    Get free GPU account at graphistry.com/get-started and
                    plug into src/docker/.env using template at envs/graphistry.env"""))
            return False


GraphistrySt()
