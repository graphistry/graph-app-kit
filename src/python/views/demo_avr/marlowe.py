"""This file marlowe.py implements utilities for using UMAP in a streamlit application.
It uses environment variables from .env and is rigorously typed."""
import logging
import os
import random
import sys
from datetime import datetime
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
DEFAULT_COLOR_BY: str = "Category"

# How to build the pivot URLs :) We will use PIVOT_URL_TEMPLATE.format(investigation_id=investigation_id, ...)
# tcook - added 00 to avoid misinterpretation on the playbook of the epoch time
PIVOT_URL_TEMPLATE: str = '<a href="/pivot/template?investigation={investigation_id}&pivot[0][events][0][general_cluster]={general_cluster}&name=Incident-360-{investigation_id}" target="_blank">Investigate Cluster</a>'

# How to cast the columns we are interested in to more useful types
AVR_SAFE_COLUMNS: Dict[str, Union[str, Type[str], Type[float]]] = {
    "DetectTime": "datetime",
    "Category": str,
    "ID": str,
    "Node_SW": str,
    "Node_Type": str,
    "Node_Name": str,
    "Source_Port": str,
    "Source_IP4": str,
    "Source_Proto": str,
    "Target_Port": str,
    "Target_IP4": str,
    "Target_Proto": str,
    "Source_IP4_Subnet_16": str,
    "Source_IP4_Subnet_24": str,
    "Target_IP4_Subnet_16": str,
    "Target_IP4_Subnet_24": str,
    "x": float,
    "y": float,
    "general_cluster": int,
    "general_probability": float,
    "specific_cluster": int,
    "specific_probability": float,
}

# FEATURE_COLUMNS = ["x", "y", "general_cluster", "specific_cluster", "general_probability", "specific_probability"]
FEATURE_COLUMNS: Optional[Union[List[str], pd.DataFrame]] = [
    "Source_IP4",
    "Target_IP4",
    "Source_Port",
    "Category",
]

# A big palette from 3 different palettes from: https://www.heavy.ai/blog/12-color-palettes-for-telling-better-stories-with-your-data
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


class AVRMissingData(Exception):
    """AVRMissingData Exception occurs when our data cleaning filters out all of the data :("""

    def __init__(self, *args, **kwargs):
        default_message = (
            "Trimming to our safe columns (or a previous operation) filtered all the data. Zero records are left."
        )

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


class AVRDataResource:
    """Filters DataFrames and hands them to AVRMarlow to visualize."""

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
        self.feature_columns: List[str] = feature_columns or list(AVR_SAFE_COLUMNS.keys())
        self.debug = debug

        # Apply all the cleaning to the edges upon instantiation
        self.trim_to_safe_cols(inplace=True)
        self.clean_edge_list(inplace=True)
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
        """trim_to_safe_cols Trim to just the AVR_SAFE_COLUMNS column names"""

        try:
            assert len(self.edf) > 0
        except AssertionError as e:
            logger.error(
                "Trimming to our safe columns (or a previous operation) filtered all the data. Zero records are left."
            )
            logger.exception(e)
            raise AVRMissingData()

        assert len(self.edf.columns) >= len(AVR_SAFE_COLUMNS.keys())
        if self.debug:
            logger.debug(
                f"Successfult assertion: len(self.edf.columns) = {len(self.edf.columns)} >= len(AVR_SAFE_COLUMNS.keys()) = {len(AVR_SAFE_COLUMNS.keys())}"
            )

        if inplace is True:
            self.edf: pd.DataFrame = self.edf[list(AVR_SAFE_COLUMNS.keys())]
        else:
            new_df: pd.DataFrame = self.edf.copy()
            return new_df[list(AVR_SAFE_COLUMNS.keys())]

    def clean_edge_list(self, inplace: bool = True) -> Optional[pd.DataFrame]:
        """clean_edge_list Clean up the edges by casting them. Makes a copy of the DataFrame to implement inplace=False."""

        new_edf: pd.DataFrame = self.edf
        # If we are not acting in place, make a copy to return. See return statement below.
        if inplace is True:
            pass
        else:
            new_edf: pd.DataFrame = self.edf.copy()

        # Cast the columns to their known types
        for col, cast in AVR_SAFE_COLUMNS.items():
            # Cast em if ya got em!
            if cast == "datetime":
                new_edf[col] = pd.to_datetime(new_edf[col], utc=True)
            elif cast == int:
                new_edf[col] = new_edf[col].fillna(-1).astype(cast)
            elif cast == float:
                new_edf[col] = new_edf[col].fillna(0.0).astype(cast)
            else:
                new_edf[col] = new_edf[col].astype(str)

        # Don't display 'nan', display None
        new_edf["Source_IP4"] = new_edf["Source_IP4"].fillna(value="None", inplace=False)
        new_edf["Source_IP4"] = new_edf["Source_IP4"].astype(str)
        new_edf["Source_IP4"] = new_edf["Source_IP4"].str.replace("nan", "None")

        new_edf["Target_IP4"] = new_edf["Target_IP4"].fillna("None", inplace=False)
        new_edf["Target_IP4"] = new_edf["Target_IP4"].astype(str)
        new_edf["Target_IP4"] = new_edf["Target_IP4"].str.replace("nan", "None")

        # Null Category fields cause the color by to fail, so we will fill them with "Unknown"
        new_edf["Category"] = new_edf["Category"].fillna("Unknown", inplace=False)

        if self.debug:
            logger.debug(f'new_edf["DetectTime"].min(): {new_edf["DetectTime"].min()}\n')
            logger.debug(f'new_edf["DetectTime"].max(): {new_edf["DetectTime"].max()}\n')

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
            logger.debug("self.feature_columns: {self.feature_columns}}")

        str_edf = self.edf[self.feature_columns]
        for col in str_edf.columns:
            str_edf[col] = str_edf[col].astype(str)

        # Concatenate the features as a string to run a topic model, and get rid of things that might come across as topics
        self.edf["features"] = (
            str_edf[self.feature_columns]
            .apply(" ".join, axis=1)  # Concatenate the values of all columns
            .str.replace("nan", "None")  # Replace nan with None
            .str.replace("None", "")  # Remove None, which covers nan and None
            .str.replace("[ ]{2,}", " ")  # Remove extra spaces
        )

        # Drop duplicates to get the nodes
        self.ndf = self.edf.drop_duplicates(subset=["features"])

        if self.debug:
            logger.debug(f"df.shape={self.edf.shape} ndf.shape={self.ndf.shape}")

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

        self.edf["pivot_url"] = self.edf["general_cluster"].apply(
            lambda x: PIVOT_URL_TEMPLATE.format(
                investigation_id=investigation_id,
                general_cluster=x,
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


class AVRMarlowe:
    """Draws Graphistries. A working man on a mission to reduce alert volume... an investigation of a cluster of authentication events."""

    def __init__(
        self,
        data_resource: AVRDataResource,
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

        logger.debug(
            f"api: {api}, protocol: {protocol} client_protocol_hostname: {client_protocol_hostname} username: {username},"
            + f" password: {password}, server: {server}, debug: {self.debug} :)\n"
        ) if self.debug else None

        graphistry.register(
            api=api,
            protocol=protocol,
            server=server,
            username=username,
            password=password,
            client_protocol_hostname=client_protocol_hostname,
        )

    def umap(
        self,
        X: Optional[Union[List[str], pd.DataFrame]] = FEATURE_COLUMNS,
        y: Optional[Union[str, List[str]]] = None,
    ) -> Plottable:
        """umap Run UMAP on the AVR edge list, visualize in 2D, unsupervised (just X) or supervised (y).

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

        if X:  # and check_type(X, List[str]): # remove type check
            try:
                if self.debug:
                    logger.debug(
                        f"assert len([x for x in X if x in self.data.edf.columns]) = {len([x for x in X if x in self.data_resource.edf.columns])}"
                        + f" == len(X) = {len(X)}"
                    )
                assert len([x for x in X if x in self.data_resource.edf.columns]) == len(X)
            except AssertionError:
                raise UMAPXColumnMissing

        if isinstance(y, str):
            y = [y]

        if self.debug:
            logger.debug(f"node data types: {self.data_resource.edf.dtypes}\n")

        # The edges are the nodes
        g: Plottable = graphistry.nodes(self.data_resource.edf)

        # Compose an HTML label of the attack category and the first 2 source/target IPs.
        g._nodes["Label"] = g._nodes.astype(str).apply(
            lambda x: f"Category: {x.Category}"
            + f"<br />Source: {' '.join(x.Source_IP4.split(' ')[:2]).strip()}"
            + f"<br />Target: {' '.join(x.Target_IP4.split(' ')[:2]).strip()}",
            axis=1,
        )

        # This Label was computed in AVRDataResource above
        if self.debug:
            logger.debug(self.data_resource.edf["Label"].head())

        g2: Plottable = g.bind(point_title="Label")

        g3: Plottable = g2.umap(
            X=FEATURE_COLUMNS,
            y=y,
            **topic_model,
        )

        g4: Plottable = g3.encode_point_color(
            DEFAULT_COLOR_BY,
            as_categorical=True,
            palette=CATEGORICAL_PALETTE,
            default_mapping="#CCC",
        )

        self.g: Plottable = g4.settings(
            url_params={
                "play": 1000,
                "strongGravity": True,
                "pointSize": 0.7,
                "pointOpacity": 0.4,
                "edgeOpacity": 0.3,
                "edgeCurvature": 0.4,
                "gravity": 0.25,
                "showPointsOfInterestLabel": False,
            }
        )

        return self.g

    def hypergraph(self, cluster_id: int = 0, render=False) -> Union[str, HTML]:
        """Visualize a hypergraph of the AVR edge list, with a specific cluster highlighted."""
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
            "Category",
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
