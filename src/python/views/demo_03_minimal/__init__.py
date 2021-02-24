import streamlit as st

# For copy/paste, 04_simple is probably better


def info():
    return {
        'id': 'app_03',
        'name': 'INTRO: minimal',
        'tags': ['demo', 'demo_intro']
    }


def run():
    st.title('app3')
    st.markdown('hello! (minimal)')
