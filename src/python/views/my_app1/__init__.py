import pandas as pd, streamlit as st
from time import sleep

from css import max_main_width, hide_dev_menu
from util.graphistry import graphistry

#######

def info():
    return {
        'id': 'app1',
        'name': 'app1',
        'enabled': True,
    }

def run():
    run_all()

#######

def plot_url(edges_df, n):
    nodes_df = pd.DataFrame({
        'n': pd.concat([edges_df['s'], edges_df['d']]).unique()
    })

    nodes_df['nc'] = nodes_df['n'].apply(lambda v: 0x01000000 * round(255 * v / n))

    return graphistry\
            .bind(source="s", destination="d")\
            .edges(edges_df)\
            .nodes(nodes_df)\
            .bind(node='n', point_color='nc')\
            .settings(url_params={
                'pointSize': 0.3,
                'splashAfter': 'false',
                'bg': '%23f0f2f6'
            })\
            .plot(render=False)


####

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters(node_type, node_range, edges_df, n):

    filtered_edges_df = edges_df
    if node_type == 'all':
        pass
    elif node_type == 'odd':
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] % 2 == 1 ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] % 2 == 1 ]
    elif node_type == 'even':
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] % 2 == 0 ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] % 2 == 0 ]
    else:
        raise Exception('Unknown filter1 option result: %s' % node_type)

    if node_range[0] > 0:
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] >= node_range[0] ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] >= node_range[0] ]
    if node_range[1] <= n:
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] <= node_range[1] ]
        filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] <= node_range[1] ]

    url = plot_url(filtered_edges_df, n)

    return filtered_edges_df, url
        

def run_all():

    _css_max_main_width()
    _css_hide_dev_menu()

    ### DATA
    st.sidebar.title('Pick graph')
    n = st.sidebar.number_input('Number of nodes', min_value=10, max_value=100000, value=100, step=20)
    #st.write('Node count', n)
    edges_df = pd.concat([
        pd.DataFrame({
            's': [x for x in range(n)],
            'd': [(x + 1) % n for x in range(n)]
        }),
        pd.DataFrame({
            's': [x for x in range(n)],
            'd': [(x + 6) % n for x in range(n)]
        })
    ], sort=False, ignore_index=True)


    ### Filter Menu
    st.sidebar.title("Filter")
    option_to_label = {
        'all': 'All',
        'odd': 'Odds',
        'even': 'Evens'
    }
    filter_by_node_type = st.sidebar.selectbox('Filter nodes by:',
        ('all', 'odd', 'even'),
        index=0, #default
        format_func=(lambda option: option_to_label[option])) 
    filter_by_node_range = st.sidebar.slider('Filter for nodes in range:',
        min_value=0, max_value=n, value=(0, n), step=1)


    filtered_edges_df, url = run_filters(filter_by_node_type, filter_by_node_range, edges_df, n)

    #### Main menu
    iframe = '<iframe src="' + url + '", height="800", width="100%" allow="fullscreen"></iframe>'
    st.markdown(iframe, unsafe_allow_html=True)
