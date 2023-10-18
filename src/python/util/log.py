import logging
import os

# logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s:%(message)s\n")
logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s:%(message)s\n")

def getChild(*args, **kwargs):

    logger = logging.getLogger('gak')

    log_level_str = os.environ.get('LOG_LEVEL', 'ERROR').upper()
    log_level = getattr(logging, log_level_str)
    logger.debug(f"util.log log_level == {log_level_str} ({log_level})")

    out=logger.getChild(*args, **kwargs)
    out.setLevel(log_level)

    out.debug(f"calling logging.setLevel() to log_level == {log_level}")

    return out
