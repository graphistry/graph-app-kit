import logging
import os

# logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s:%(message)s\n")
logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s:%(message)s\n")

def getChild(*args, **kwargs):

    logger = logging.getLogger('gak')

    if "LOG_LEVEL" in os.environ:
        log_level=getattr(logging, os.environ["LOG_LEVEL"].upper())
    else:
        log_level=getattr(logging,logging.ERROR)

        logger.debug(f"util.log envar LOG_LEVEL: {os.environ['LOG_LEVEL']}")
        logger.debug(f"util.log log_level == {log_level}")

    out=logger.getChild(*args, **kwargs)
    out.setLevel(log_level)

    out.debug(f"calling logging.setLevel() to log_level == {log_level}")

    return out
