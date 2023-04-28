import os
from typing import Callable, TypeVar

import pandas as pd
import pytest
from typeguard import typechecked

from app import clean_edge_list, AVR_SAFE_COLUMNS
from marlowe import AVRDataResource, AVRMarlowe
from splunk import SplunkConnection

graphistry_username: str = os.getenv("GRAPHISTRY_USERNAME")
graphistry_password: str = os.getenv("GRAPHISTRY_PASSWORD")
graphistry_protocol: str = os.getenv("GRAPHISTRY_PROTOCOL")
graphistry_host: str = os.getenv("GRAPHISTRY_HOSTNAME")
print(graphistry_username, graphistry_password, graphistry_protocol, graphistry_host)
splunk_username: str = os.getenv("SPLUNK_USERNAME")
splunk_password: str = os.getenv("SPLUNK_PASSWORD")
splunk_host: str = os.getenv("SPLUNK_HOST")
print(splunk_username, splunk_password, splunk_host)


def test_splunk_env():
    """Verify our Splunk credentials are set before going any further."""
    f: Callable[[str], bool] = lambda x: x is not None and isinstance(x, str) and len(x) > 5
    for field in [splunk_username, splunk_password, splunk_host]:
        assert f(field)


def test_graphistry_env():
    """Verify our Graphistry credentials are set before going any further."""
    f: Callable[[str], bool] = (
        lambda x: x is not None and isinstance(x, str) and len(x) >= 4
    )  # http
    for field in [graphistry_username, graphistry_password, graphistry_protocol, graphistry_host]:
        assert f(field)


@pytest.fixture
def get_test_edf() -> pd.DataFrame:
    """get_df Fixture that returns an edge list pd.DataFrame"""
    df: pd.DataFrame = pd.DataFrame(
        {
            "ID": [str(x) for x in range(1, 10)],
            "src_domain": [str(x) for x in range(1, 10)],
            "dst_domain": [str(x) for x in range(1, 10)],
        }
    )
    return df


@pytest.fixture
def get_real_df() -> pd.DataFrame:
    """get_real_df Load a real pd.DataFrame from /data/grouped_alert.csv"""
    return pd.read_csv("/data/grouped_alert.csv", low_memory=False)


@pytest.fixture
def get_data_resource(get_real_df: pd.DataFrame) -> AVRDataResource:
    """get_data_resource Fixture that gets a marlowe.AVRDataResource from a real edge list.

    Parameters
    ----------
    get_df : pd.DataFrame
        An edge DataFrame

    Returns
    -------
    AVRDataResource
        A data resource
    """
    return AVRDataResource(get_real_df)


@pytest.fixture
def get_marlowe(get_real_df: pd.DataFrame) -> AVRMarlowe:
    """get_marlowe Get a visual investigator."""
    return AVRMarlowe(get_real_df)


@pytest.fixture
def get_splunk() -> SplunkConnection:
    return SplunkConnection(host=splunk_host, username=splunk_username, password=splunk_password)


@pytest.fixture
def get_query() -> str:
    query_field_str = " ".join(AVR_SAFE_COLUMNS)
    return f"search index=avr_59k | fields {query_field_str}"


@typechecked
def test_type_hints(
    get_test_edf: pd.DataFrame,
    get_real_df: pd.DataFrame,
    get_data_resource: AVRDataResource,
    get_marlowe: AVRMarlowe,
) -> None:
    """test_type_hints Test of tests and fixtures: Do I even remember pytest types?"""
    assert isinstance(get_test_edf, pd.DataFrame)
    assert isinstance(get_real_df, pd.DataFrame)
    assert isinstance(get_data_resource, AVRDataResource)
    assert isinstance(get_marlowe, AVRMarlowe)


@typechecked
def test_series_filter(get_data_resource: AVRDataResource):
    """Test if AVRMarlowe data filtering works"""
    bool_series: TypeVar("pd.Series(bool") = get_data_resource.edf["general_cluster"] < 5

    # Check the pd.DataFrame returned by inplace=False
    df: pd.DataFrame = get_data_resource.filter(bool_series, inplace=False)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(bool_series[bool_series])

    # Now check inplace=True
    get_data_resource.filter(bool_series, inplace=True)
    assert len(get_data_resource.edf) == len(bool_series[bool_series])
    assert (bool_series.index[bool_series] == get_data_resource.edf.index).all()


def test_env_umap(get_marlowe: AVRMarlowe, get_data_resource: AVRDataResource) -> None:
    """Test the UMAP code to make sure it runs ok."""
    df = get_data_resource.edf.sample(1000)

    marlowe = AVRMarlowe(df)

    marlowe.register(
        username=graphistry_username,
        password=graphistry_password,
        protocol=graphistry_protocol,
        host=graphistry_host,
        api=3,
    )

    graph_url = marlowe.umap(render=False)

    assert isinstance(graph_url, str) and (len(graph_url) > 7)
    assert AVRDataResource.is_url(graph_url)


def test_one_shot_splunk(get_splunk: SplunkConnection, get_query: str) -> None:
    """Test the SplunkConnection.one_shot_splunk()"""

    df = get_splunk.one_shot_splunk(get_query)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1000

    for field in AVR_SAFE_COLUMNS:
        assert field in df

    # The -1 cluster is a random noise cluster
    clusters = sorted(df["general_cluster"].fillna(-1).astype(int).drop_duplicates())
    assert max(clusters) >= 0


def test_splunk_query(get_splunk: SplunkConnection, get_query: str) -> None:
    """test_splunk_query Test the main query method."""

    r = get_splunk.query(get_query)
    assert len(r) == 50000


def test_cast_avr_data(get_real_df) -> pd.DataFrame:
    """test_cast_avr_data Test casting the data as in app.py"""

    df = clean_edge_list(get_real_df)
    assert len(df) > 0


# equality_query
