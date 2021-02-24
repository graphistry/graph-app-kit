import logging, os

logger = logging.getLogger()
logger.setLevel(
    logging.getLevelName(os.environ['LOG_LEVEL'])
    if 'LOG_LEVEL' in os.environ else
    logging.ERROR)


def getChild(*args, **kwargs):
    return logger.getChild(*args, **kwargs)
