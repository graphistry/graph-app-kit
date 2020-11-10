# Develop graph-app-kit dashboard views

## Setup

## Recommended: Web authoring

Not required but recommended, we recommend setting up Jupyter-based shared web authoring. You can proceed without, such as live editing from a commandline tool like `vim`. However, if you are interested in a friendlier environment, see the [configuration and integrations section](extend.md).

## Live edit

* Modify Python files in `src/python/views/[your dashboard]/__init__.py`, and in-tool, hit the `rerun` button that appears
* Add new views by adding `views/[your dsahboard]/__init__.py` with methods `def info(): return {'name': 'x'}` and `def run(): None`
* Add new dependencies: modify `src/python/requirements-app.txt` and rerun `docker-compose build` and restart

## Toggle views

Configure which dashboards `AppPicker` includes:

* Disable individual dashboards: Have a dashboard's `info()` return `{'enabled': False}`
* Create tags and toggle them: 
  * Tag a dashboard view as part of `src/python/views/[your_app]/__init__.py`:
     * `info()`: `{'tags': ['new_app', ...]}`
  * Opt-in and opt-out to tags: in `src/python/entrypoint.py`:
    * `AppPicker(include=['testing', 'new_app'], exclude=['demo'])`

## Toggle view CSS defaults
Use the `css` module in your `views`:

```python
from css import all_css
def run():
  all_css()
  all_css(is_max_main_width=False, is_hide_dev_menu=False)
```

## Configure site theme
Tweak `src/python/entrypoint.py`:

```python
page_title_str ="Graph dashboard"
st.beta_set_page_config(
	layout="centered",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
	page_title=page_title_str,  # String or None. Strings get appended with "• Streamlit". 
	page_icon='none.png',  # String, anything supported by st.image, or None.
)
```

## Extend!

You are now ready to [add integrations](extend.md) like database connections, authentication, and live editing.