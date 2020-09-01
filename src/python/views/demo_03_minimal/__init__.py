import streamlit as st

# For copy/paste, 04_simple is probably better

def info():
    return {
        'id': 'app_03',
        'name': 'app3: minimal'
    }


def run():
    st.title('app3')
    st.markdown('hello! (minimal)')
    
