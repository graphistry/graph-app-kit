import streamlit as st
import SessionState

from util import getChild, load_modules
logger = getChild(__name__)


####
VIEW_INDEX_VAR="view_index"

###
query_params = st.experimental_get_query_params()
session_state = SessionState.get(first_query_params=query_params)
first_query_params = session_state.first_query_params


###

modules_by_id = load_modules()

####
maybe_default_view_index = eval(first_query_params[VIEW_INDEX_VAR][0]) if VIEW_INDEX_VAR in first_query_params else None

###
if len(modules_by_id.keys()) == 0:
    st.sidebar.header('Create src/views/myapp/__init__.py::run()')
else:
    view = None
    if len(modules_by_id.keys()) == 1:
        view_id = modules_by_id.values()[0]['id']
        view = modules_by_id[view_id]
    else:
        sorted_mods = sorted(modules_by_id.values(), key=lambda nfo: nfo['i'])
        view_id = st.sidebar.selectbox('',
            [nfo['id'] for nfo in sorted_mods],
            index=0 if maybe_default_view_index is None else maybe_default_view_index,
            format_func=(lambda id: modules_by_id[id]['name'].upper()))
        view = modules_by_id[view_id]
        query_params[VIEW_INDEX_VAR] = sorted_mods.index(sorted_mods[view_id])
        st.experimental_set_query_params(**query_params)
        st.sidebar.title(view['name'])
    st.title(view)
    modules_by_id[view_id].run()