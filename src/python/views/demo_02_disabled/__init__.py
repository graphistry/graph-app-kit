import streamlit as st


def info():
    return {
        'id': 'app_02',
        'name': 'INTRO: disabled',
        'enabled': False,
        'tags': ['demo', 'demo_intro']
    }


def run():
    st.title('app2')
    st.markdown('hello! (disabled: not visible in menu)')
