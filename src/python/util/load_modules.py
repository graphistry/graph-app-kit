import importlib, os

def load_modules():
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
        sorted_mods[i]['i'] = i
    return modules_by_id
    