import graphistry, pandas as pd, streamlit as st
from components import GraphistrySt, URLParam
from css import all_css
from util import getChild

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'fincen'
logger = getChild(app_id)
urlParams = URLParam(app_id)


def info():
    return {
        'id': app_id,
        'name': 'FinCEN',
        'tags': ['prod']
    }


def run():
    run_all()


############################################
#
#   PIPELINE PIECES
#
############################################


# Have fun!
def custom_css():
    all_css()
    st.markdown(
        """<style>

        </style>""", unsafe_allow_html=True)


# Given URL params, render left sidebar form and return combined filter settings
# https://docs.streamlit.io/en/stable/api.html#display-interactive-widgets
def sidebar_area():

    # regular param (not in url)
    # e = st.sidebar.number_input('Number of edges', min_value=10, max_value=100000, value=100, step=20)

    # deep-linkable param (in url)
    # n_init = urlParams.get_field('N', 100)
    # n = st.sidebar.number_input('Number of nodes', min_value=10, max_value=100000, value=n_init, step=20)
    # urlParams.set_field('N', n)

    with st.sidebar:

        st.markdown('Data from [ICIJ](https://www.icij.org/investigations/fincen-files/)')

        transactions_df = fetch_csv()
        banks = pd.concat([ transactions_df['originator_bank_id'], transactions_df['beneficiary_bank_id'] ]).unique()
        banks.sort()
        bank_ids = st.multiselect('Show banks with IDs', ['(off)'] + banks.tolist())

        b_init = urlParams.get_field('B', 'Rosbank')
        bank = st.text_input('Show banks with name like', b_init)
        urlParams.set_field('B', bank)

    return {'num_nodes': 1000000, 'num_edges': 1000000, 'bank': bank, 'bank_ids': bank_ids}


@st.cache(suppress_st_warning=True, allow_output_mutation=True, hash_funcs={pd.DataFrame: lambda _: None})
def fetch_iso3611():
    return pd.read_csv('https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv')


@st.cache(suppress_st_warning=True, allow_output_mutation=True, hash_funcs={pd.DataFrame: lambda _: None})
def fetch_csv():
    from io import BytesIO
    from urllib.request import urlopen
    from zipfile import ZipFile

    zip_url = 'https://media.icij.org/uploads/2020/09/download_data_fincen_files.zip'
    zip_dir = '/tmp/download_data_fincen_files'
    with urlopen(zip_url) as zipresp:
        with ZipFile(BytesIO(zipresp.read())) as zfile:
            zfile.extractall(zip_dir)

    transactions_map_df = pd.read_csv(f'{zip_dir}/download_transactions_map.csv')
    transactions_map_df['begin_date'] = pd.to_datetime(transactions_map_df['begin_date'])
    transactions_map_df['end_date'] = pd.to_datetime(transactions_map_df['end_date'])
    return transactions_map_df


# graph of (x in ids) -> y
def ego_edges(nodes, edges, ids, src, dst, node):
    df = edges
    # ego<>neighbor
    direct = pd.concat(
        [ edges[:0] ] + [ df[(df[src] == id) | (df[dst] == id)] for id in ids ],
        ignore_index=True, sort=False)

    # ego | neighbor
    ns = pd.concat([
            direct[[src]].rename(columns={src: 'id'}),
            direct[[dst]].rename(columns={dst: 'id'})
        ], sort=False, ignore_index=True)\
        .drop_duplicates()

    # (ego|neighbor)<>(ego|neighbor)
    ego_edges = pd.concat([
        df.merge(ns.rename(columns={'id': src}), how='inner', on=src),
        df.merge(ns.rename(columns={'id': dst}), how='inner', on=dst)],
        ignore_index=True,
        sort=False).drop_duplicates()

    neighborhood_ns = pd.DataFrame({'id': list(set(ego_edges[src].unique().tolist() + ego_edges[dst].unique().tolist()))})

    # ego|neighbor
    ego_nodes = nodes.merge(neighborhood_ns.rename(columns={'id': node}), how='inner', on=node)
    return ego_nodes, ego_edges


def bank_name_to_ids(df, bank, bank_ids):

    filtered = df

    bank_name_filter = bank if len(bank) > 0 and not (bank == '(off)') and not (bank == '') else None
    bank_id_filter = [x for x in bank_ids if x != '(off)']

    if (not (bank_name_filter is None)) or (len(bank_id_filter) > 0):
        hits = filtered['bank_id'] == 'no hits'
        if not (bank_name_filter is None):
            hits = filtered['bank'].str.contains(bank_name_filter, case=False)
        for id in bank_id_filter:
            hits = hits | (filtered['bank_id'] == id)
        filtered = filtered[ hits ]

    return filtered['bank_id'].unique().tolist()


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(suppress_st_warning=True, allow_output_mutation=True, hash_funcs={pd.DataFrame: lambda _: None})
def run_filters(num_nodes, num_edges, bank, bank_ids):

    transactions_map_df = fetch_csv()

    # GLOBAL STATS

    sample_df = transactions_map_df  # .sample(10000)

    originator_stats_df = sample_df.groupby('originator_bank_id').agg({
        'begin_date': 'min',
        'end_date': 'max',
        'number_transactions': ['sum', 'max'],
        'amount_transactions': ['sum', 'max']})
    originator_stats_df.columns = ['originator_' + '_'.join(tup).rstrip('_') for tup in originator_stats_df.columns]
    originator_stats_df = originator_stats_df.reset_index().rename(columns={'originator_bank_id': 'bank_id'})

    beneficiary_stats_df = sample_df.groupby('beneficiary_bank_id').agg({
        'begin_date': 'min',
        'end_date': 'max',
        'number_transactions': ['sum', 'max'],
        'amount_transactions': ['sum', 'max']})
    beneficiary_stats_df.columns = ['beneficiary_' + '_'.join(tup).rstrip('_') for tup in beneficiary_stats_df.columns]
    beneficiary_stats_df = beneficiary_stats_df.reset_index().rename(columns={'beneficiary_bank_id': 'bank_id'})

    originator_cols = [c for c in sample_df.columns if 'originator_' in c]
    beneficiary_cols = [c for c in sample_df.columns if 'beneficiary_' in c]

    nodes_df = pd.concat(
        [
            sample_df[originator_cols]
                .rename(columns={c: c.replace("originator_", "") for c in originator_cols})
                .drop_duplicates(subset=['bank_id'])
                .assign(type='bank', entity_id=sample_df['originator_bank_id']),
            sample_df[beneficiary_cols]
                .rename(columns={c: c.replace("beneficiary_", "") for c in beneficiary_cols})
                .drop_duplicates(subset=['bank_id'])
                .assign(type='bank')
                .assign(type='bank', entity_id=sample_df['beneficiary_bank_id'])
        ],
        ignore_index=True, sort=False)

    nodes_df = nodes_df\
        .merge(beneficiary_stats_df, on='bank_id', how='left')\
        .merge(originator_stats_df, on='bank_id', how='left')
    nodes_df['abbreviation'] = nodes_df['bank'].apply(lambda s: ''.join([x[:1] for x in s.split(" ")[:3]]))

    nodes_df['sum_transactions'] = \
        nodes_df['originator_amount_transactions_sum'].fillna(0) \
        + nodes_df['beneficiary_amount_transactions_sum'].fillna(0)
    nodes_df['number_transactions'] = \
        nodes_df['originator_number_transactions_sum'].fillna(0) \
        + nodes_df['beneficiary_number_transactions_sum'].fillna(0)

    iso3611_df = fetch_iso3611()
    iso3_to_iso2 = {
        row['ISO3166-1-Alpha-3'].lower(): row['ISO3166-1-Alpha-2'].lower()
        for row in iso3611_df[['ISO3166-1-Alpha-2', 'ISO3166-1-Alpha-3']].to_dict(orient='records')
        if ('ISO3166-1-Alpha-3' in row and type(row['ISO3166-1-Alpha-3']) == str)
            and ('ISO3166-1-Alpha-2' in row and type(row['ISO3166-1-Alpha-2']) == str)
    }
    nodes_df['iso2'] = nodes_df['iso'].apply(lambda v: iso3_to_iso2[v.lower()] if v.lower() in iso3_to_iso2 else '')
    iso2_to_flags = {
        iso2: 'flag-icon-' + iso2
        for iso2 in nodes_df['iso2'].unique()
    }

    # PROJECTION

    ids = bank_name_to_ids(nodes_df, bank, bank_ids)
    ego_banks_df = nodes_df.merge(pd.DataFrame({'entity_id': ids}), how='inner')
    nodes_df, sample_df = ego_edges(
        nodes_df, sample_df, ids,
        src='originator_bank_id', dst='beneficiary_bank_id', node='entity_id')

    # VIZ

    # abbrv_to_abbrv = {x: x for x in nodes_df['abbreviation'].unique().tolist()}
    bank_to_bank = {x: x for x in nodes_df['bank'].unique().tolist()}

    g = graphistry.edges(sample_df).nodes(nodes_df)\
        .bind(source='originator_bank_id', destination='beneficiary_bank_id', node='entity_id')\
        .bind(point_title='bank', point_size='sum_transactions')\
        .encode_point_icon('bank', as_text=True, categorical_mapping=bank_to_bank)\
        .encode_point_badge('iso2', 'TopRight', categorical_mapping=iso2_to_flags)\
        .encode_point_color(
            'beneficiary_amount_transactions_sum',
            palette=['white', 'pink', 'purple'],
            as_continuous=True,
            for_current=True)\
        .encode_edge_color(
            'amount_transactions',
            ["maroon", "red", "yellow", "white", "cyan"],
            as_continuous=True,
            for_current=True)\
        .addStyle(bg={'color': '#EEE'})\
        .settings(
            height=800,
            url_params={
                'pointOpacity': 0.3 if len(sample_df) > 1500 else 1.0,
                'edgeOpacity': 0.2 if len(sample_df) > 1500 else 1.0,
                'strongGravity': True,
                'showPointsOfInterestLabel': False,
                'play': 5000})

    graph_url = g.plot(render=False)
    return { 'nodes_df': g._nodes, 'edges_df': g._edges, 'graph_url': graph_url, 'ego_banks_df': ego_banks_df }


def main_area(num_nodes, num_edges, bank, bank_ids, nodes_df, edges_df, graph_url, ego_banks_df):

    logger.debug('rendering main area, with url: %s', graph_url)
    GraphistrySt().render_url(graph_url)

    st.subheader('Selected banks')
    st.write(ego_banks_df)
    st.subheader('Surrounding banks')
    st.write(nodes_df)
    st.subheader('Reported transactions')
    st.write(edges_df)


############################################
#
#   PIPELINE FLOW
#
############################################


def run_all():

    custom_css()

    try:

        # Render sidebar and get current settings
        sidebar_filters = sidebar_area()

        # Compute filter pipeline (with auto-caching based on filter setting inputs)
        # Selective mark these as URL params as well
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings
        main_area(**sidebar_filters, **filter_pipeline_result)

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
