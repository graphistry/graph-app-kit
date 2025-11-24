import logging
import os
import sys

# logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s:%(message)s\n")
logging.basicConfig(format="%(levelname)s %(asctime)s %(name)s:%(message)s\n")

def getChild(*args, **kwargs):

    logger = logging.getLogger('gak')

    log_level_str = os.environ.get('LOG_LEVEL', 'ERROR').upper()
    # Handle non-standard log levels gracefully
    try:
        log_level = getattr(logging, log_level_str)
    except AttributeError:
        # Map non-standard levels to closest standard level
        level_mapping = {
            'TRACE': logging.DEBUG,
            'VERBOSE': logging.DEBUG,
        }
        log_level = level_mapping.get(log_level_str, logging.ERROR)
        sys.stderr.write(f"Log level '{log_level_str}' not supported, mapping to {logging.getLevelName(log_level)}\n")
    logger.debug(f"util.log log_level == {log_level_str} ({log_level})")

    out=logger.getChild(*args, **kwargs)
    out.setLevel(log_level)

    out.debug(f"calling logging.setLevel() to log_level == {log_level}")

    return out
