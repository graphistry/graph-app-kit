import json
import urllib
import streamlit as st
import logging

from util import getChild

logger = getChild(__name__)

class URLParam:
    def __init__(self, prefix="d_"):
        self.prefix = prefix

    # str * 'a -> 'a
    def get_field(self, field: str, default=None):
        field = self.prefix + field
        query_params = st.query_params.to_dict()
        maybe_v = json.loads(urllib.parse.unquote(query_params[field])) if field in query_params else None
        out = default if maybe_v is None else maybe_v
        logger.debug("resolved default for %s as %s :: %s", field, out, type(out))
        return out

    # str * 'a -> ()
    def set_field(self, field: str, val):
        field = self.prefix + field
        query_params = st.query_params.to_dict()
        logger.debug("params at set: %s", query_params.items())
        logger.debug("rewriting field %s val %s as %s", field, val, urllib.parse.quote(json.dumps(val), safe=""))

        new_value = urllib.parse.quote(json.dumps(val), safe="")
        # Only update if the value has changed to prevent infinite loops
        if field not in query_params or query_params[field] != new_value:
            new_params = {**{k: v for k, v in query_params.items()}, **{field: new_value}}
            st.query_params.from_dict(new_params)
