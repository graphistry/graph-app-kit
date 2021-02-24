import streamlit as st


# Full width for main area
# https://discuss.streamlit.io/t/custom-render-widths/81/6
def max_main_width():
    max_width_str = f"max-width: 2000px;"
    st.markdown(
        f"""
            <style>
            .reportview-container .main .block-container{{
                {max_width_str}
            }}

            .reportview-container .main .block-container:first-child {{
                padding-top: 0;
                margin-top: 0;
            }}
            </style>
        """,
        unsafe_allow_html=True)


# Hide dev menu
def hide_dev_menu():
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def all_css(is_max_main_width=True, is_hide_dev_menu=True):
    if is_max_main_width:
        max_main_width()
    if is_hide_dev_menu:
        hide_dev_menu()
