"""This file marlowe.py implements utilities for using UMAP in a streamlit application.
It uses environment variables from .env and is rigorously typed."""
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Type, TypeVar, Union
from urllib.parse import urlparse

import dateutil.parser as dp
import graphistry
import numpy as np
import pandas as pd
from graphistry.features import topic_model
from graphistry.Plottable import Plottable
from IPython.core.display import HTML

logger = logging.getLogger(__name__)

# Reproducible samples
SEED = 31337
random.seed = SEED
np.random.seed = SEED

# Where to store and load the UMAP model for the topic model
UMAP_MODEL_PATH = ".models/umap.topic"

# Default categorical field to use to draw color on the nodes
DEFAULT_COLOR_BY: str = "dbscan"

# How to build the pivot URLs :) We will use PIVOT_URL_TEMPLATE.format(investigation_id=investigation_id, ...)
PIVOT_URL_TEMPLATE: str = '<a href="/pivot/template?investigation={investigation_id}&pivot[0][events][0][src_computer]={src_computer}&name=Incident-360-{investigation_id}" target="_blank">Investigate Source Computer</a>'

# How to cast the columns we are interested in to more useful types
AUTH_SAFE_FIELDS: Dict[str, Union[str, Type[str], Type[float]]] = {
    "RED": float,
    "auth_type": str,
    "authentication_orientation": str,
    "cluster": int,
    "dst_computer": str,
    "dst_domain": str,
    "is_anomalous": bool,
    "logontype": str,
    "node": int,
    "probability": float,
    "src_computer": str,
    "src_domain": str,
    "success_or_failure": str,
    "datetime": "datetime",
    "time": int,
}

# FEATURE_COLUMNS = ["x", "y", "general_cluster", "specific_cluster", "general_probability", "specific_probability"]
FEATURE_COLUMNS: Optional[Union[List[str], pd.DataFrame]] = [
    "src_computer",
    "dst_computer",
]

# A big palette from 3 different palettes from:
# https://www.heavy.ai/blog/12-color-palettes-for-telling-better-stories-with-your-data
CATEGORICAL_PALETTE: List[str] = (
    [
        "#ea5545",
        "#f46a9b",
        "#ef9b20",
        "#edbf33",
        "#ede15b",
        "#bdcf32",
        "#87bc45",
        "#27aeef",
        "#b33dc6",
    ]
    + [
        "#b30000",
        "#7c1158",
        "#4421af",
        "#1a53ff",
        "#0d88e6",
        "#00b7c7",
        "#5ad45a",
        "#8be04e",
        "#ebdc78",
    ]
    + [
        "#fd7f6f",
        "#7eb0d5",
        "#b2e061",
        "#bd7ebe",
        "#ffb55a",
        "#ffee65",
        "#beb9db",
        "#fdcce5",
        "#8bd3c7",
    ]
)


class UMAPXColumnMissing(ValueError):
    """UMAPXColumnMissing Exception occurs when X values given to Plottable.umap() are not in given pd.DataFrame."""

    def __init__(self, *args, **kwargs):
        default_message = "Not all columns in X are in our edge list :("

        # if no arguments are passed set the first positional argument
        # to be the default message. To do that, we have to replace the
        # 'args' tuple with another one, that will only contain the message.
        # (we cannot do an assignment since tuples are immutable)
        # If you inherit from the exception that takes message as a keyword
        # maybe you will need to check kwargs here
        if not args:
            args = (default_message,)

        # Call super constructor
        super().__init__(*args, **kwargs)


class AuthMissingData(Exception):
    """AuthMissingData Exception occurs when our data cleaning filters out all of the data :("""

    def __init__(self, *args, **kwargs):
        default_message = """Trimming to our safe columns (or a previous operation) filtered all the data.
        Zero records (rows) are left."""

        # if no arguments are passed set the first positional argument
        # to be the default message. To do that, we have to replace the
        # 'args' tuple with another one, that will only contain the message.
        # (we cannot do an assignment since tuples are immutable)
        # If you inherit from the exception that takes message as a keyword
        # maybe you will need to check kwargs here
        if not args:
            args = (default_message,)

        # Call super constructor
        super().__init__(*args, **kwargs)


class AuthDataResource:
    """Filters DataFrames and hands them to AuthMarlow to visualize."""

    def __init__(
        self,
        edf: pd.DataFrame,
        feature_columns: List[str],
        debug: bool = False,
    ) -> None:
        """__init__ Instantiate a DataFrame handler.

        Parameters
        ----------
        edf : pd.DataFrame
            DataFrame to use as edges and extract features and nodes from
        feature_columns : List[str]
            A list of column names to build features from via concatenation and topic modeling
        debug : bool, optional
            True = print debug messages, False = don't, by default False
        """

        self.edf: pd.DataFrame = edf

        logging.debug(f"Origial edf.shape: {edf.shape}")
        logging.debug(f"Origial edf.columns: {edf.columns}")

        self.feature_columns: List[str] = feature_columns or list(AUTH_SAFE_FIELDS.keys())
        self.debug = debug

        # Apply all the cleaning to the edges upon instantiation
        self.trim_to_safe_cols(inplace=True)
        self.clean_edge_list(inplace=True)
        self.add_datetime()
        # ...and set deduped edge features as nodes
        self.featurize_edges()

    def filter(self, bool_series: TypeVar("pd.Series(bool)"), inplace: bool = False) -> Union[None, pd.DataFrame]:
        """filter Filter our DataFrame using a boolean Series, optionally in place.

        Parameters
        ----------
        f : pd.Series[bool], optional
            A boolean pandas pd.Series to filter a DataFrame, by default None
        inplace : bool, optional
            True = alter self.edf, False = return a new edf, by default False

        Returns
        -------
        pd.DataFrame
            A filtered DataFrame.
        """

        # Filter data QA
        assert len(bool_series) == len(self.edf)
        assert (bool_series.index == self.edf.index).all()

        if inplace:
            self.edf = self.edf[bool_series]
            return None
        else:
            return self.edf[bool_series]

    def trim_to_safe_cols(self, inplace: bool = True) -> Optional[pd.DataFrame]:
        """trim_to_safe_cols Trim to just the AUTH_SAFE_FIELDS column names"""

        try:
            assert len(self.edf) > 0
        except AssertionError as e:
            logger.exception(e)
            raise AuthMissingData(
                "Trimming to our safe columns (or a previous operation) filtered all the data. Zero records are left."
            )

        if self.debug:
            logger.debug(f"self.edf.columns: {self.edf.columns}\n")
            logger.debug(
                f"len(self.edf.columns): {len(self.edf.columns)} | len(AUTH_SAFE_FIELDS.keys()): {len(AUTH_SAFE_FIELDS.keys())}\n"
            )

        assert len(self.edf.columns) >= len(AUTH_SAFE_FIELDS.keys())

        if self.debug:
            logger.debug(
                f"Successfult assertion: len(self.edf.columns) = {len(self.edf.columns)} >="
                + f"len(AUTH_SAFE_FIELDS.keys()) = {len(AUTH_SAFE_FIELDS.keys())}\n"
            )

        if inplace is True:
            self.edf: pd.DataFrame = self.edf[list(AUTH_SAFE_FIELDS.keys())]
        else:
            new_df: pd.DataFrame = self.edf.copy()
            return new_df[list(AUTH_SAFE_FIELDS.keys())]

    def add_datetime(self) -> None:
        """add_datetime Add a datetime column to our DataFrame using the timeframe and an offset."""
        # Make the time a 2023 datetime
        offset_date = datetime.now() - timedelta(days=30)
        seconds_offset = time.mktime(offset_date.timetuple())
        self.edf["datetime"] = pd.to_datetime(self.edf["time"] + seconds_offset, unit="s")

    def clean_edge_list(self, inplace: bool = True) -> Optional[pd.DataFrame]:
        """clean_edge_list Clean up the edges by casting them. Makes a copy of the DataFrame to implement
        inplace=False."""

        new_edf: pd.DataFrame = self.edf
        # If we are not acting in place, make a copy to return. See return statement below.
        if inplace is True:
            pass
        else:
            new_edf: pd.DataFrame = self.edf.copy()

        # Cast the columns to their known types
        for col, cast in AUTH_SAFE_FIELDS.items():
            # Cast em if ya got em!
            if cast == "datetime":
                new_edf[col] = pd.to_datetime(new_edf[col], utc=True)
            elif cast == int:
                new_edf[col] = new_edf[col].fillna(0).astype(cast)
            elif cast == float:
                new_edf[col] = new_edf[col].fillna(0.0).astype(cast)
            else:
                new_edf[col] = new_edf[col].astype(str)

        # Don't display 'nan', display None
        new_edf["src_domain"] = new_edf["src_domain"].fillna(value="None", inplace=True)
        new_edf["src_domain"] = new_edf["src_domain"].astype(str)
        new_edf["src_domain"] = new_edf["src_domain"].str.replace("nan", "None")

        new_edf["dst_domain"] = new_edf["dst_domain"].fillna("None", inplace=True)
        new_edf["dst_domain"] = new_edf["dst_domain"].astype(str)
        new_edf["dst_domain"] = new_edf["dst_domain"].str.replace("nan", "None")

        # We sum it, so we need this
        new_edf["is_anomalous"] = new_edf["is_anomalous"].astype(bool).astype(int)

        if inplace is True:
            self.edf: pd.DataFrame = new_edf
        else:
            # Since we assigned new_edf a copy of self.edf, we intend to return it :)
            return new_edf

    def featurize_edges(self) -> None:
        """featurize_edges generate a string feature column and deduplicate it to get nodes

        Parameters
        ----------
        debug : bool, optional, by default False
            True = print debug statements, False = don't print debug statements
        """

        # Dedupe for safety
        self.feature_columns = self.feature_columns
        if self.debug:
            logger.debug("self.feature_columns: {self.feature_columns}}\n")

        str_edf = self.edf[self.feature_columns]
        for col in str_edf.columns:
            str_edf[col] = str_edf[col].astype(str)

        # Concatenate the features as a string to run a topic model, and get rid of things that might come
        # across as topics
        self.edf["features"] = (
            str_edf[self.feature_columns]
            .apply(" ".join, axis=1)  # Concatenate the values of all columns
            .str.replace("nan", "None")  # Replace nan with None
            .str.replace("None", "")  # Remove None, which covers nan and None
            .str.replace(r"\s+", " ", regex=True)  # Remove extra spaces
        )

        # Drop duplicates to get the nodes
        self.ndf = self.edf.drop_duplicates(subset=["features"])

        if self.debug:
            logger.debug(f"df.shape={self.edf.shape} ndf.shape={self.ndf.shape}\n")

    def add_pivot_url_column(
        self,
        investigation_id: str,
    ) -> None:
        """add_pivot_url_column Add a pivot url column using the investigation_id, general_cluster

        Parameters
        ----------
        investigation_id : str
            The identifier of the visual playbook template to which the URL refers

        Returns
        -------
        A url pd.Series[str] or None, by default None. Depends on whether inplace is True or False.
            The Void™
        """

        self.ndf["pivot_url"] = self.ndf["src_computer"].apply(
            lambda x: PIVOT_URL_TEMPLATE.format(
                investigation_id=investigation_id,
                src_computer=x,
            )
        )

    @staticmethod
    def is_url(url: str) -> bool:
        """is_url True if a valid URL is passed, otherwise False

        Parameters
        ----------
        url : str
            A url to validate

        Returns
        -------
        bool
            True (url is valid) or False(url is not valid)
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def iso_to_unix(iso_date: str) -> float:
        """iso_to_unix Convert an ISO8601 datetime to a Unix timestamp

        Parameters
        ----------
        iso_date : str
            An ISO8601 datetime

        Returns
        -------
        float
            Seconds since January 1st, 1970 at UTC
        """
        dt = dp.parse(iso_date)
        return dt.timestamp()

    @staticmethod
    def unix_to_iso(unix_ts: float) -> str:
        """unix_to_iso_to_unix Convert a unix timestamp to an ISO8601 datetime in UTC timezone and back

        Parameters
        ----------
        unix_ts : float
            Seconds since January 1st, 1970 at UTC

        Returns
        -------
        str
            An ISO8601 datetime
        """
        return datetime.utcfromtimestamp(unix_ts).isoformat()


class AuthMarlowe:
    """Draws Graphistries. A working man on a mission to reduce alert volume... an investigation
    of a cluster of authentication events."""

    def __init__(
        self,
        data_resource: AuthDataResource,
        debug: bool = False,
    ) -> None:
        """__init__ Instantiate a visual investigator.

        Parameters
        ----------
        data : AWRDataResource
            An instance of AWRDataResource containing nodes and edges
        debug : bool, optional, by default False
            True = print debug statements, False = don't print debug statements
        """
        self.data_resource = data_resource
        self.g: Optional[Plottable] = None
        self.debug = debug

    def register(
        self,
        protocol: str,
        server: str,
        username: str,
        password: str,
        client_protocol_hostname: Optional[str] = None,
        api: Optional[Literal[1, 3]] = 3,
    ) -> None:
        self.protocol = protocol
        self.server = server
        self.client_protocol_hostname = client_protocol_hostname
        self.api = api

        graphistry.register(
            api=api,
            protocol=protocol,
            server=server,
            username=username,
            password=password,
            client_protocol_hostname=client_protocol_hostname,
        )

    def cluster_anomaly_counts(self) -> pd.DataFrame:
        """Count the anomalies per cluster and return a DataFrame of the results sorted descending on anomaly count."""

        # Compute the total anomalies per cluster within the anomalous nodes
        self.anomalous_nodes = self.g._nodes[self.g._nodes["cluster"] == -1]

        anom_cluster_counts = (
            self.anomalous_nodes[["dbscan", "is_anomalous", "RED"]]
            .groupby("dbscan")
            .agg({"is_anomalous": "sum", "RED": "sum"})
        )
        anom_cluster_counts.reset_index(inplace=True)
        anom_cluster_counts.rename(
            columns={
                "dbscan": "anomaly_cluster",
                "is_anomalous": "anomaly_count",
                "RED": "RED",
            },
            inplace=True,
        )

        if self.debug:
            logger.debug(f"anom_cluster_counts.index = {anom_cluster_counts.index}\n")
            logger.debug(f"anom_cluster_counts.columns = {anom_cluster_counts.columns}\n")

        if self.debug:
            logger.debug(f"Total anom_cluster_counts = {len(anom_cluster_counts)}\n")

        return anom_cluster_counts

    def cluster_top_nodes(self, n: int = 5) -> pd.Series:
        """Create a list of the top n most anomalous computers by src_computer column."""

        anomalous_cpu_clusters = (
            self.anomalous_nodes.groupby(["src_computer", "dbscan"])
            .count()
            .reset_index()
            .rename(columns={"src_computer": "computer", "dbscan": "anomaly_cluster"})
        )

        # Get the count of anomalies per computer - ndf is a deduplicated edge list of src/dst computers
        return anomalous_cpu_clusters.groupby("anomaly_cluster")["computer"].apply(lambda x: list(x)[:n])

    def describe_clusters(self) -> pd.DataFrame:
        """Describe the clusters in the data we ingested and return a DataFrame of the results."""

        # Compute the pieces of the DataFrame and then stitch them together
        anom_cluster_counts = self.cluster_anomaly_counts()

        # Compute the most anomalous nodes per cluster
        top_n_computers = self.cluster_top_nodes()

        # Join anom_cluster_counts and top_n_computers
        self.cluster_df = (
            anom_cluster_counts.merge(
                top_n_computers,
                on="anomaly_cluster",
                how="left",
            )
            .sort_values("anomaly_count", ascending=False)
            .set_index("anomaly_cluster")
        )

        return self.cluster_df

    def umap(
        self,
        X: Optional[Union[List[str], pd.DataFrame]] = FEATURE_COLUMNS,
        y: Optional[Union[str, List[str]]] = None,
    ) -> Plottable:
        """umap Run UMAP on the Auth edge list, visualize in 2D, unsupervised (just X) or supervised (y).

        Parameters
        ----------
        X : Optional[Union[List[str], pd.DataFrame]], optional
            The pd.DataFrame columns to use in the topic model, by default Non, in which case UMAP will use all columns
        y : Optional[Union[List[str]]], optional
            The fields to supervise the clustering, by default None
        render : bool, optional
            For the final plot, render a Graphistry (True) or return a URL (False), by default False
        debug : bool, optional
            Whether to log debug output, by default False

        Returns
        -------
        graphistry.Plottable
            A graphistry Plottable object, returned by Plottable.umap()
        """

        if X and isinstance(X, list):
            try:
                if self.debug:
                    column_count = len([x for x in X if x in self.data_resource.edf.columns])
                    logger.debug(
                        f"assert len([x for x in X if x in self.data.edf.columns]) = {column_count}"
                        + f" == len(X) = {len(X)}\n"
                    )
                assert len([x for x in X if x in self.data_resource.edf.columns]) == len(X)
            except AssertionError:
                raise UMAPXColumnMissing

        if isinstance(y, str):
            y = [y]

        if self.debug:
            logger.debug(f"node data types: {self.data_resource.edf.dtypes}\n")

        # The edges are the nodes
        g: Plottable = (
            graphistry.nodes(self.data_resource.ndf)
            .edges(self.data_resource.edf)
            .bind(point_title="features")  # , point_size="all_anomalous")
        )

        # I won't work after the previous line - g._nodes isn't there yet
        #

        # Compose an HTML label of the attack category and the first 2 source/target IPs.
        g._nodes["Label"] = g._nodes.astype(str).apply(
            lambda x: f"Source: {x.src_computer}<br />Dest: {x.dst_computer}",
            axis=1,
        )

        # This Label was computed in AuthDataResource above
        if self.debug:
            logger.debug(f'{self.data_resource.edf["Label"].head()}\n')

        g2: Plottable = g.bind(point_title="Label")

        g3: Plottable = g2.umap(
            X=FEATURE_COLUMNS,
            y=y,
            dbscan=True,
            **topic_model,
        )

        # Rename the _dbscan column to be ok with Splunk
        g3._nodes.rename(columns={"_dbscan": "dbscan"}, inplace=True)

        g4: Plottable = g3.encode_point_color(
            DEFAULT_COLOR_BY,
            as_categorical=True,
            palette=CATEGORICAL_PALETTE,
            default_mapping="gray",
        )

        self.g = g4.settings(
            url_params={
                "play": 0,
                "strongGravity": True,
                "pointSize": 0.3,
                "pointOpacity": 0.2,
                "edgeOpacity": 0.15,
                "edgeCurvature": 0.4,
                "gravity": 0.5,
                "showPointsOfInterestLabel": False,
                "height": 200,
            },
            height=200,
        )

        return self.g

    def hypergraph(self, cluster_id: int = 0, render=False) -> Union[str, HTML]:
        """Visualize a hypergraph of the Auth edge list, with a specific cluster highlighted."""
        gen_cluster_filter = self.edf["general_cluster"] > -1
        spec_cluster_filter = self.edf["specific_cluster"] > -1
        hyper_edf = self.edf[gen_cluster_filter & spec_cluster_filter]

        g = graphistry.hypergraph(
            hyper_edf,
            ["Source_IP4", "Target_IP4", "ID", "general_cluster", "specific_cluster"],
            direct=True,
            opts={
                "EDGES": {
                    "Source_IP4": ["Target_IP4"],  # , "ID", "general_cluster", "specific_cluster"],
                    # "general_cluster": ["Target_IP4"],
                },
                "CATEGORIES": {"IP4": ["Source_IP4", "Target_IP4"]},
            },
        )["graph"]

        self.g = g.encode_point_color(
            "category",
            as_categorical=True,
            categorical_mapping={
                "ID": "red",
                "IP4": "lightblue",
                "general_cluster": "lightgrey",
                "specific_cluster": "darkgrey",
            },
            default_mapping="#CCC",
        )
        self.g = self.g.settings(url_params={"play": 1000, "strongGravity": True, "pointOpacity": 0.6})

        return self.g.plot(render=render)
