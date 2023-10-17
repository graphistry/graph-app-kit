import graphistry, os, pandas as pd, streamlit as st
from components import GraphistrySt, URLParam
from graphistry import PyGraphistry
from css import all_css
from time import sleep
import logging

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'app_00'
logger = logging.getLogger(app_id)
urlParams = URLParam(app_id)


def info():
    return {
        'id': app_id,
        'name': 'Bio: FUNCOUP',
        'enabled': True,
        'tags': ['bio', 'large', 'funcoup','demo'],
    }


def run():
    run_all()


############################################
#
#   CUSTOM CSS
#
############################################
# Have fun!

def custom_css():

    all_css()  # our favorites


############################################
#
#   SIDEBAR RENDER AERA
#
############################################
# Given URL params, render left sidebar form and return combined filter settings

# #https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area():
    st.sidebar.title("Pick an Organism")
    species_to_label = {
        'A.thaliana': 'A.thaliana',
        'B.subtilis': 'B.subtilis',
        'B.taurus': 'B.taurus',
        'C.elegans': 'C.elegans',
        'C.familiaris': 'C.familiaris',
        'C.intestinalis': 'C.intestinalis',
        'D.discoideum': 'D.discoideum',
        'D.melanogaster': 'D.melanogaster',
        'D.rerio': 'D.rerio',
        'E.coli': 'E.coli',
        'G.gallus': 'G.gallus',
        'H.sapiens': 'H.sapiens',
        'M.jannascii': 'M.jannascii',
        'M.musculus': 'M.musculus',
        'O.sativa': 'O.sativa',
        'P.falciparum': 'P.falciparum',
        'R.norvegicus': 'R.norvegicus',
        'S.cerevisiae': 'S.cerevisiae',
        'S,pombe': 'S.pombe',
        'S.scrofa': 'S.scrofa',
        'S.solfataticus': 'S.solfataricus',
    }

    base_url = os.environ['BASE_URL']

    filter_by_org_type_init = urlParams.get_field('filter_by_org', default='H.sapiens')
    filter_by_org_type = \
        st.sidebar.selectbox(
            'Choose species:',
            ('A.thaliana', 'B.subtilis', 'B.taurus','C.elegans','C.familiaris','C.intestinalis','D.discoideum','D.melanogaster','D.rerio','E.coli','G.gallus','H.sapiens','M.jannascii','M.musculus','O.sativa','P.falciparum','R.norvegicus','S.cerevisiae','S,pombe','S.scrofa','S.solfataticus'),
            index=('A.thaliana', 'B.subtilis', 'B.taurus','C.elegans','C.familiaris','C.intestinalis','D.discoideum','D.melanogaster','D.rerio','E.coli','G.gallus','H.sapiens','M.jannascii','M.musculus','O.sativa','R.norvegicus','S.cerevisiae','S,pombe','S.scrofa','S.solfataticus').index(filter_by_org_type_init),
            format_func=(lambda option: species_to_label[option]))
    urlParams.set_field('filter_by_org', filter_by_org_type)


    st.sidebar.title("Edge Type")
    edge_to_label = {
        'PFC': 'The confidence Score',
        'FBS_max': 'The final Bayesian Score (FBS) of the strongest coupling class',
        'FBS_*': 'Bayesian Score of all coupling classes',
        'LLR_*': 'Log Likelihood Ratio (LLRs) of the different evidence types',
        'LLR_*': 'LLRs of the evidence types from the differrent species',
        'Max_category': 'strongest couping class for this pair. This is also the class for which the LLRs are given'
    }

    filter_by_node_type_init = urlParams.get_field('filter_by_node', default='PFC')
    filter_by_node_type = \
        st.sidebar.selectbox(
            'Filter node by:',
            ('PFC','FBS_max','FBS_*','LLR_*','LLR_*','Max_category'),
            index=('PFC','FBS_max','FBS_*','LLR_*','LLR_*','Max_category').index(filter_by_node_type_init),
            format_func=(lambda option: edge_to_label[option]))
    urlParams.set_field('filter_by_node', filter_by_node_type)


    st.sidebar.title("Net Type")
    net_to_label = {
        'compact': 'compact',
        'full': 'full',
    }

    filter_by_net_type_init = urlParams.get_field('filter_by_net', default='compact')
    filter_by_net_type = \
        st.sidebar.selectbox(
            'Filter net by:',
            ('compact','full'),
            index=('compact','full').index(filter_by_net_type_init),
            format_func=(lambda option: net_to_label[option]))
    urlParams.set_field('filter_by_net', filter_by_net_type)


    st.sidebar.title("Umap Type")
    umap_to_label = {
        True: True,
        False: False,
    }

    filter_by_umap_type_init = urlParams.get_field('filter_by_umap', default=False)
    filter_by_umap_type = \
        st.sidebar.selectbox(
            'Filter umap by:',
            (True,False),
            index=(True,False).index(filter_by_umap_type_init),
            format_func=(lambda option: umap_to_label[option]))
    urlParams.set_field('filter_by_umap', filter_by_umap_type)
    
    # edges_df = pd.read_csv('https://funcoup.org/downloads/download.action?type=network&instanceID=24480085&fileName=FC5.0_B.taurus_compact.gz', sep='\t')
    edges_df = pd.read_csv('https://funcoup.org/downloads/download.action?type=network&instanceID=24480085&fileName=FC5.0_'+filter_by_org_type+'_'+filter_by_net_type+'.gz', sep='\t')

    return {
        'edges_df': edges_df,
        # 'org_type': filter_by_org_type,
        # 'node_type': filter_by_node_type,
        # 'net_type': filter_by_net_type,
        'umap_type': filter_by_umap_type,
    }


############################################
#
#   FILTER PIPELINE
#
############################################
# Given filter settings, generate/cache/return dataframes & viz

#@st.cache(suppress_st_warning=True, allow_output_mutation=True)
@st.cache_data
def run_filters(edges_df,umap_type=False):

    filtered_edges_df = edges_df[:100000] #[['2:Gene1','3:Gene2','1:FBS_max','#0:PFC']]
    filtered_edges_df = filtered_edges_df.replace({'ENSG00000':''},regex=True)
    # filtered_edges_df.rename(columns={'2:Gene1':'Gene1','3:Gene2':'Gene2','#0:PFC':'PFC','1:FBS_max':'FBS'},inplace=True)
    filtered_edges_df.columns=filtered_edges_df.columns.str.split(':').str[1]
    # filtered_edges_df = edges_df
    # if node_type == 'all':
    #     pass
    # elif node_type == 'odd':
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] % 2 == 1 ]
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] % 2 == 1 ]
    # elif node_type == 'even':
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] % 2 == 0 ]
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] % 2 == 0 ]
    # else:
    #     raise Exception('Unknown filter1 option result: %s' % node_type)

    # if node_range[0] > 0:
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] >= node_range[0] ]
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] >= node_range[0] ]
    # if node_range[1] <= n:
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['s'] <= node_range[1] ]
    #     filtered_edges_df = filtered_edges_df[ filtered_edges_df['d'] <= node_range[1] ]

    # include viz generation as part of cache
    url = plot_url(filtered_edges_df,umap_type)

    return {
        'edges_df': filtered_edges_df,
        'url': url
    }


############################################
#
#   VIZ
#
############################################


def plot_url(edges_df,umap_type=False):

    nodes_df = pd.DataFrame({
        'n': pd.concat([edges_df['Gene1'], edges_df['Gene2']]).unique()
    })
    n = len(nodes_df)

    nodes_df['nc'] = nodes_df['n'].replace('ENSG00000','',regex=True)
    nodes_df['nc'] = pd.to_numeric(nodes_df['nc'], errors='coerce')
    nodes_df['nc'] = nodes_df['nc'].fillna(0).apply(lambda v: 0x01000000 * round(255 * v / n))

    logger.info('Starting graphistry plot')
    if not GraphistrySt().test_login():
        return ''
    
    if umap_type == False:
        url = graphistry\
                .edges(edges_df)\
                .bind(source="Gene1", destination="Gene2")\
                .nodes(nodes_df)\
                .bind(node='n', point_color='nc')\
                .settings(url_params={
                    'pointSize': 0.3,
                    'splashAfter': 'false',
                    'bg': '%23' + 'f0f2f6'
                })\
                .plot(render=False)
    elif umap_type == True:
        url = graphistry\
                .edges(edges_df)\
                .bind(source="Gene1", destination="Gene2")\
                .nodes(nodes_df)\
                .bind(node='n', point_color='nc')\
                .settings(url_params={
                    'pointSize': 0.3,
                    'splashAfter': 'false',
                    'bg': '%23' + 'f0f2f6'
                })\
                .umap(engine='umap_learn')\
                .plot(render=False)

    logger.info('Generated viz, got back urL: %s', url)

    return url


############################################
#
#   MAIN RENDER AERA
#
############################################
# Given configured filters and computed results (cached), render

def main_area(edges_df, url):

    logger.debug('rendering main area, with url: %s', url)
    gst = GraphistrySt()
    if PyGraphistry._is_authenticated:
        gst.render_url(url)
    else:
        st.title("Welcome to graph-app-kit!")
        st.write("""
            This particular demo requires configuring your graph-app-kit with service credentials for
            accessing your Graphistry server

            If this is the first time you are seeing graph-app-kit, it is Graphistry's open-source extension
            of the https://streamlit.io/ low-code Python dashboarding tool. It adds:
              * Optional Docker, Docker Compose, and AWS CloudFormation self-hosted quick launchers
              * Multiple dashboard support
              * Optional GPU & AI dependencies (Nvidia driver, RAPIDS, PyTorch) aligned with Graphistry releases
              * Graph computing dependencies (Gremlin, TigerGraph, ...)
              * A Graphistry plotting component

            Starting with Graphistry 2.39, graph-app-kit comes prebundled:
              * Public and staff-only Private dashboards
              * Control access via User -> Admin port -> DJANGO-WAFFLE -> Flags"
              * ... then edit to desired visibility for flag_show_public_dashboard, flag_show_private_dashboard
              * ... and optionally prevent running of the services via your docker-compose.override.yml
        """)


############################################
#
#   Putting it all together
#
############################################

def run_all():

    custom_css()

    try:

        # Render sidebar and get current settings
        sidebar_filters = sidebar_area()

        # logger.debug('sidebar_filters: %s', sidebar_filters)

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(**filter_pipeline_result)

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
