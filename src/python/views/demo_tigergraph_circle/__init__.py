import asyncio, datetime, graphistry, pandas as pd, \
    plotly.express as px, pyTigerGraphBeta as tg, \
    streamlit as st, time

from components import GraphistrySt, URLParam
from css import all_css
from TigerGraph_helper import tg_helper
from util import getChild

############################################
#
#   DASHBOARD SETTINGS
#
############################################
#  Controls how entrypoint.py picks it up


app_id = 'tigergraph_circle'
logger = getChild(app_id)
urlParams = URLParam(app_id)
node_id_col = 'id'
src_id_col = 'from_id'
dst_id_col = 'to_id'
node_label_col = 'Source_Type'
edge_label_col = 'Destination_Type'

# Setup a structure to hold metrics
metrics = {'tigergraph_time': 0, 'graphistry_time': 0,
           'node_cnt': 0, 'edge_cnt': 0, 'prop_cnt': 0}


# Define the name of the view
def info():
    return {
        'id': app_id,
        'name': 'TigerGraph: Fraud Filter circle',
        'tags': ['demo', 'tigergraph_demo_circle']
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

    logger.info('sidebar_area')

    st.sidebar.subheader('Select account for 360 view')
    idList = [i for i in range(1, 500)]
    user_id = st.sidebar.selectbox('User ID ', idList)
    urlParams.set_field('user_id', user_id)

    # Optional, can replace with: conn = tg_helper.connect_to_tigergraph()
    conn = None
    st.sidebar.subheader('Optional: Override tigergraph.env')
    tg_host = st.sidebar.text_input('TigerGraph Host')
    tg_username = st.sidebar.text_input('TigerGraph Username')
    tg_password = st.sidebar.text_input('TigerGraph Password', type='password')
    tg_secret = st.sidebar.text_input('TigerGraph Secret', type='password')
    tg_graphname = st.sidebar.text_input('TigerGraph Graphname')
    if st.sidebar.button("Connect"):
        try:
            conn = tg.TigerGraphConnection(
                host=tg_host, graphname=tg_graphname, username=tg_username, password=tg_password,
                version=tg_helper.TIGERGRAPH_CONNECTION_VERSION)
            if tg_secret:
                conn.getToken(tg_secret)
            else:
                conn.getToken(conn.createSecret())
        # FIXME: What is the expected exn?
        except Exception as e:  # noqa: E722
            logger.error('Failed dynamic tg connection: %s', e, exc_info=True)
            st.sidebar.error("Failed to Connect")
            st.sidebar.error(e)
            return None
    else:
        conn = tg_helper.connect_to_tigergraph()
    if conn is None:
        logger.error('Cannot run tg demo without creds')
        st.write(RuntimeError('Demo requires a TigerGraph connection. Put creds into left sidebar, or fill in envs/tigergraph.env & restart'))
        return None

    st.sidebar.success("Connnected Successfully")
    return {'user_id': user_id, 'conn': conn}


def plot_url(nodes_df, edges_df):

    logger.info('Starting graphistry plot')
    tic = time.perf_counter()

    # edge weight ( ==> score )
    # edgeInfluence @ https://hub.graphistry.com/docs/api/1/rest/url/#urloptions

    g = graphistry \
        .edges(edges_df) \
        .settings(url_params={'play': 7000, 'dissuadeHubs': True}) \
        .bind(edge_weight='amount')      \
        .bind(source='from_id', destination='to_id') \
        .bind(edge_title='amount', edge_label='amount') \
        .nodes(nodes_df) \
        .bind(node='n') \
        .addStyle(bg={'color': 'white'}) \
        .encode_point_color("type", categorical_mapping={'User': 'orange',
                                                         'Transaction': '#CCC'},
                                    default_mapping='black') \
        .encode_edge_color("type", categorical_mapping={'User_Transfer_Transaction': 'black',
                                                        'User_Recieve_Transaction_Rev': '#add836'},
                                    default_mapping='black') \
        .encode_point_icon('type', categorical_mapping={'User': 'laptop',
                                                        'Transaction': 'server'},
                                    default_mapping='question')

    # .encode_point_size('', ["blue", "yellow", "red"],  ,as_continuous=True)
    # if not (node_label_col is None):
    #     g = g.bind(point_title=node_label_col)

    # if not (edge_label_col is None):
    #     g = g.bind(edge_title=edge_label_col)

    url = g.plot(render=False, as_files=True)

    toc = time.perf_counter()
    metrics['graphistry_time'] = toc - tic
    logger.info(f'Graphisty Time: {metrics["graphistry_time"]}')
    logger.info('Generated viz, got back urL: %s', url)

    return url


# Given filter settings, generate/cache/return dataframes & viz
@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def run_filters(user_id, conn):  # noqa: C901

    logger.info("Installing Queries")
    logger.info('Graph name: %s, user_id: %s', conn.graphname, user_id)
    try:
        res = conn.gsql(
        '''
        use graph {}
        ls
        '''.format(conn.graphname), options=[])
    except SystemExit as e:
        logger.error('Failed listing graph queries %s', e, exc_info=True)
        st.write('Failed listing graph queries')
        st.write(e)
        raise e
    except Exception as e:
        logger.error('Failed on `use graph` test: %s', e, exc_info=True)
        st.write(e)
        raise e

    ind = res.index('Queries:') + 1
    installTran = True
    for query in res[ind:]:
        if 'totalTransaction' in query:
            installTran = False

    if installTran:
        conn.gsql(
        '''
        use graph AntiFraud
        CREATE QUERY totalTransaction(Vertex<User> Source) FOR GRAPH AntiFraud {
            start = {Source};

            transfer = SELECT tgt
                FROM start:s -(User_Transfer_Transaction:e) - :tgt;

            receive = select tgt
                FROM start:s -(User_Recieve_Transaction:e) -:tgt;

            PRINT transfer, receive;
        }
        Install query totalTransaction
        ''', options=[])

    logger.info('Querying Tigergraph')
    tic = time.perf_counter()

    raw_results = conn.runInstalledQuery("circleDetection", {"srcId": user_id}, sizeLimit=1000000000, timeout=120000)
    results = raw_results[0]['@@circleEdgeTuples']

    # FIXME: Automate
    out = []
    from_ids = []
    to_ids = []
    times = []
    amounts = []
    types = []
    from_types = []
    to_types = []
    for o in results:
        for s in o:
            if {
                "from_id": s["e"]["from_id"], "to_id": s["e"]["to_id"], "amount": s["amount"], "time": s["ts"],
                "type": s["e"]["e_type"]
            } not in out:
                out.append(
                    {"from_id": s["e"]["from_id"], "to_id": s["e"]["to_id"], "amount": s["amount"], "time": s["ts"],
                     "type": s["e"]["e_type"]})
                from_ids.append(s["e"]["from_id"])
                to_ids.append(s["e"]["to_id"])
                amounts.append(s["amount"])
                times.append(s["ts"])
                types.append(s["e"]["e_type"])
                from_types.append(s['e']['from_type'])
                to_types.append(s['e']['from_type'])

    edges_df = pd.DataFrame({
        'from_id': from_ids,
        'to_id': to_ids,
        'amount': amounts,
        'time': times,
        'type': types
    })
    node_idf = []
    typef = []
    for i in range(len(from_ids)):
        if from_ids[i] not in node_idf:
            node_idf.append(from_ids[i])
            typef.append(from_types[i])
        if to_ids[i] not in node_idf:
            node_idf.append(to_ids[i])
            typef.append(to_types[i])

    nodes_df = pd.DataFrame({
        'n': node_idf,
        'type': typef,
        'size': 0.1
    })

    try:
        res = nodes_df.values.tolist()
        toc = time.perf_counter()
        logger.info(f'Query Execution: {toc - tic:0.02f} seconds')
        logger.debug('Query Result Count: %s', len(res))
        metrics['tigergraph_time'] = toc - tic

        # Calculate the metrics
        metrics['node_cnt'] = nodes_df.size
        metrics['edge_cnt'] = edges_df.size
        metrics['prop_cnt'] = (nodes_df.size * nodes_df.columns.size) + \
                              (edges_df.size * edges_df.columns.size)

        if nodes_df.size > 0:
            url = plot_url(nodes_df, edges_df)
        else:
            url = ""
    except Exception as e:
        logger.error('oops in TigerGraph', exc_info=True)
        raise e
    logger.info("Finished compute phase")

    try:
        pass

    except RuntimeError as e:
        if str(e) == "There is no current event loop in thread 'ScriptRunner.scriptThread'.":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        else:
            raise e

    except Exception as e:
        logger.error('oops in TigerGraph', exc_info=True)
        raise e

    return {'nodes_df': nodes_df, 'edges_df': edges_df, 'url': url, 'res': res, 'conn': conn}


def main_area(url, nodes, edges, user_id, conn):

    logger.info('rendering main area, with url: %s', url)
    GraphistrySt().render_url(url)

    dates = []
    amounts = []
    transfer_type = []
    results = None

    try:
        results = conn.runInstalledQuery("totalTransaction", params={"Source": user_id})[0]
    except Exception as e:
        print(e)

    # Create bar chart of transactions
    if results is not None:
        for action in results:
            for transfer in results[action]:
                dates.append(datetime.datetime.fromtimestamp(transfer['attributes']['ts']))
                amounts.append(transfer['attributes']['amount'])
                transfer_type.append(action)
        cols = list(zip(dates, amounts, transfer_type))
        cols = sorted(cols, key=lambda x: x[0].day)
        cols = sorted(cols, key=lambda x: x[0].month)
        cols = sorted(cols, key=lambda x: x[0].year)
        df = pd.DataFrame(data=cols, columns=['Date', 'Amount', 'Type'])
        df['Date'] = pd.to_datetime(df['Date'])
        map_color = {"receive": "rgba(0,0,255,0.5)", "transfer": "rgba(255,0,0,0.5)"}
        df['Color'] = df['Type'].map(map_color)

        df = df.groupby([df['Date'].dt.to_period('M'), 'Type', 'Color']).sum()
        df = df.reset_index(level=['Type', 'Color'])
        df.index = df.index.values.astype('datetime64[M]')
        bar = px.bar(df, x=df.index, y='Amount', labels={'x': 'Date'}, color='Type', color_discrete_map=map_color,
                     text='Amount', title="Transaction Amounts by Month for User {}".format(user_id), height=350,
                     barmode='group')
        bar.update_xaxes(
            dtick="M1",
            tickformat="%b\n%Y")
        try:
            for trace in bar.data:
                trace.name = trace.name.split('=')[1].capitalize()
        # FIXME exepct exn?
        except:  # noqa: E722
            for trace in bar.data:
                trace.name = trace.name.capitalize()

        st.plotly_chart(bar, use_container_width=True)

    st.markdown(f'''<small>
            TigerGraph Load Time (s): {float(metrics['tigergraph_time']):0.2f} |
            Graphistry Load Time (s): {float(metrics['graphistry_time']):0.2f} |
            Node Count: {metrics['node_cnt']} |
            Edge Count: {metrics['edge_cnt']} |
            Property Count: {metrics['prop_cnt']}
        </small>''', unsafe_allow_html=True)


############################################
#
#   PIPELINE FLOW
#
############################################


def run_all():
    logger.info('run_all')

    custom_css()

    try:

        # Render sidebar, get current settings and TG connection
        sidebar_filters = sidebar_area()

        # Stop if not connected to TG
        if sidebar_filters is None:
            return

        # Compute filter pipeline, with auto-caching based on filter setting inputs
        filter_pipeline_result = run_filters(**sidebar_filters)

        # Render main viz area based on computed filter pipeline results and sidebar settings if data is returned
        if filter_pipeline_result['nodes_df'].size > 0:
            main_area(filter_pipeline_result['url'],
                      filter_pipeline_result['nodes_df'],
                      filter_pipeline_result['edges_df'],
                      sidebar_filters['user_id'],
                      filter_pipeline_result['conn'])
        else:  # render a message
            st.write("No data matching the specfiied criteria is found")

    except Exception as exn:
        st.write('Error loading dashboard')
        st.write(exn)
