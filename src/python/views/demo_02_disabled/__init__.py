import streamlit as st


def info():
    return {
        'id': 'app_02',
        'name': 'app2: disabled',
        'enabled': False
    }

def run():
    st.title('app2')
    st.markdown('hello! (disabled: not visible in menu)')
    
