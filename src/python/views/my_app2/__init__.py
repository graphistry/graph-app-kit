import streamlit as st


def info():
    return {
        'name': 'app2',
        'enabled': False
    }

def run():
    st.title('app2')
    st.markdown('hello!')
    
