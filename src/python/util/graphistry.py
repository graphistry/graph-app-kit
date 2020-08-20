import graphistry, os

def config(overrides={}):
    cfg = {
        'api': 3,
        **({'username': os.environ['GRAPHISTRY_USERNAME']} if 'GRAPHISTRY_USERNAME' in os.environ else {}),
        **({'password': os.environ['GRAPHISTRY_PASSWORD']} if 'GRAPHISTRY_PASSWORD' in os.environ else {}),
        **({'protocol': os.environ['GRAPHISTRY_PROTOCOL']} if 'GRAPHISTRY_PROTOCOL' in os.environ else {}),
        **({'server': os.environ['GRAPHISTRY_SERVER']} if 'GRAPHISTRY_SERVER' in os.environ else {}),
        **({'client_protocol_hostname': os.environ['GRAPHISTRY_CLIENT_PROTOCOL_HOSTNAME']} if 'GRAPHISTRY_CLIENT_PROTOCOL_HOSTNAME' in os.environ else {}),
        **overrides
    }
    graphistry.register(**cfg)

config()