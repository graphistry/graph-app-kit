import streamlit as st
from components import AppPicker

page_title_str = "Graph dashboard"
st.set_page_config(
    layout="centered",  # Can be "centered" or "wide". In the future also "dashboard", etc.
    initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
    page_title=page_title_str,  # String or None. Strings get appended with "• Streamlit".
    page_icon='none.png',  # String, anything supported by st.image, or None.
)

# loads all views/<app>/__init__.py and tracks active as URL param "?view_index=<info()['id']>"
#  includes modules with methods run()
#  and excludes if ('enabled' in info() and info()['enabled'] == False)
#  ... and further include/exclude via info()['tags']
AppPicker().load_active_app()

# AppPicker(include=[], exclude=['demo']).load_active_app()
