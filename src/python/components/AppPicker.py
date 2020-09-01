import importlib, os, streamlit as st

from util import getChild
logger = getChild(__name__)

#loads all views/<app>/__init__.py and tracks active as URL param "?view_index=<info()['id']>"
#  includes modules with methods run() 
#  and excludes if ('enabled' in info() and info()['enabled'] == False)
class AppPicker:
    VIEW_APP_ID_VAR="view_index"

    def __init__(self):
        pass

    # () -> {'id' -> { 'name': str, 'id': str, 'module': Module } }
    def list_modules(self):
        modules_by_id = {}
        for view_folder in sorted([view.split('/')[-1] for (view,_,_) in os.walk('/apps/views') if view != '/apps/views']):
            mod = importlib.import_module(f'views.{view_folder}')
            if hasattr(mod, 'run'):
                nfo = mod.info() if hasattr(mod, 'info') else {'name': view_folder}
                if ('enabled' in nfo) and not nfo['enabled']:
                    continue
                mod_id = nfo['id'] if 'id' in nfo else nfo['name']
                modules_by_id[mod_id] = {
                    'name': view_folder,
                    **nfo,
                    'id': mod_id,
                    'module': mod,
                }
        sorted_mods = sorted(modules_by_id.values(), key=lambda nfo: nfo['id'])
        for i in range(len(sorted_mods)):
            sorted_mods[i]['index'] = i
        return modules_by_id
        
    
    # () -> ? str
    def get_maybe_active_view_id(self, query_params):
        maybe_default_view_id = query_params[self.VIEW_APP_ID_VAR][0] if self.VIEW_APP_ID_VAR in query_params else None
        return maybe_default_view_id


    # () -> ? { 'name': str, 'id': str, 'module': Module }
    def get_and_set_active_app(self):

        query_params = st.experimental_get_query_params()
        maybe_default_view_id = self.get_maybe_active_view_id(query_params)
        logger.debug('url view id: %s', maybe_default_view_id)

        modules_by_id = self.list_modules()
        logger.debug('loaded mods: %s', modules_by_id)

        view = None
        if len(modules_by_id.keys()) == 0:
            pass        
        else:
            if len(modules_by_id.keys()) == 1:
                view_id = list(modules_by_id.values())[0]['id']
                view = modules_by_id[view_id]
            else:
                sorted_mods = sorted(modules_by_id.values(), key=lambda nfo: nfo['index'])
                view_id = st.sidebar.selectbox(
                    '',
                    [nfo['id'] for nfo in sorted_mods],
                    index=0 if maybe_default_view_id is None else modules_by_id[maybe_default_view_id]['index'],
                    format_func=(lambda id: modules_by_id[id]['name'].upper()))
                view = modules_by_id[view_id]
                query_params[self.VIEW_APP_ID_VAR] = view_id
                st.experimental_set_query_params(**query_params)

        return view

    def load_active_app(self):

        mods = self.list_modules()
        view = self.get_and_set_active_app()
        
        if len(mods.keys()) == 0:
            st.sidebar.header('Create src/views/myapp/__init__.py::run()')
        elif len(mods.keys()) == 1:
            pass
        else:
            st.sidebar.title(view['name'])

        if not (view is None):
            logger.info('running mod: %s / %s', view, view['module'])
            view['module'].run()

        return view