import importlib, os, streamlit as st
import SessionState


query_params = st.experimental_get_query_params()
app_state = st.experimental_get_query_params()
session_state = SessionState.get(first_query_params=query_params)
first_query_params = session_state.first_query_params


apps = sorted([app.split('/')[-1] for (app,_,_) in os.walk('/apps/apps') if app != '/apps/apps'])
modules = {app: importlib.import_module(f'apps.{app}') for app in apps}
modules = {app: modules[app] for app in modules.keys() if hasattr(modules[app], 'run')}
app_names = [app.info()['name'] for app in modules.values()]

maybe_default_app_index = eval(first_query_params["app_index"][0]) if "app_index" in first_query_params else None

if len(modules.keys()) == 0:
    st.sidebar.header('Create src/apps/myapp/__init__.py::run()')
else:
    app = None
    if len(modules.keys()) == 1:
        app = modules.keys()[0]
    else:
        app = st.sidebar.selectbox('',
            app_names,
            index=0 if maybe_default_app_index is None else maybe_default_app_index,
            format_func=(lambda option: option.upper()))
        app_state["app_index"] = app_names.index(app)
        st.experimental_set_query_params(**app_state)
        st.sidebar.title(app)
    st.title(app)
    list(modules.values())[app_state["app_index"]].run()
