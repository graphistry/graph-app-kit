import logging
import os
import streamlit.logger

streamlit.logger.get_logger = logging.getLogger
streamlit.logger.setup_formatter = None
streamlit.logger.update_formatter = lambda *a, **k: None
streamlit.logger.set_log_level = lambda *a, **k: None

# https://github.com/streamlit/streamlit/issues/4742#issuecomment-1130917745
# Then set our logger in a normal way
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(name)s:%(message)s",
    #force=True,
)  # Change these settings for your own purpose, but keep force=True at least

streamlit_handler = logging.getLogger("streamlit")
streamlit_handler.setLevel(logging.DEBUG)

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

    out.debug(f"util.log.getChild setLevel to log_level_views == {log_level}")

    return out
