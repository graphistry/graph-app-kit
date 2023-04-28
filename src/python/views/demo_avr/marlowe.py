import logging
import random
import sys
from typing import List, TypeVar, Union
from urllib.parse import urlparse

import graphistry
import numpy as np
import pandas as pd
from typeguard import typechecked
from IPython.core.display import HTML

from views.demo_avr.colors import categorical_palette

# Reproducible samples
SEED = 31337
random.seed = SEED
np.random.seed = SEED

# Setup better logging to STDERR and a file if we miss what happend.
logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logging.StreamHandler(sys.stderr)


class AVRDataResource:
    """Filters DataFrames and hands them to AVRMarlow to visualize."""

    @typechecked
    def __init__(
        self,
        edf: pd.DataFrame,
    ) -> None:
        """__init__ Instantiate a DataFrame handler.

        Parameters
        ----------
        edf : pd.DataFrame
            DataFrame to hold on to.
        """

        self.edf = edf

    @typechecked
    def filter(
        self, bool_series: TypeVar("pd.Series(bool)"), inplace: bool = False
    ) -> Union[None, pd.DataFrame]:
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

    @staticmethod
    @typechecked
    def is_url(url: str) -> bool:
        """is_url True if a valid URL is passed, otherwise False

        Parameters
        ----------
        url : str
            A url to validate

        Returns
        -------
        _type_
            True (url is valid) or False(url is not valid)
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False


class UMAPXColumnMissing(ValueError):
    """Exception occures when X values given to Plotter.umap() are not in given pd.DataFrame."""

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


class AVRMarlowe:
    """Draws Graphistries. A working man on a mission to reduce alert volume... an investigation of a cluster of authentication events."""

    @typechecked
    def __init__(
        self,
        edf: pd.DataFrame,
    ) -> None:
        """__init__ Instantiate a visual investigator.

        Parameters
        ----------
        edf : pd.DataFrame
            A DataFrame to draw.
        """
        self.edf: pd.DataFrame = edf
        self.g: Union[None, graphistry.plotter.Plotter] = None

    @typechecked
    def register(
        self,
        username: str,
        password: str,
        protocol: str,
        host: str,
        api: int = 3,
        client_protocol_hostname: str = None, 
        debug=False,
    ) -> None:
        logger.warning(
            f"API: {api}, GRAPHISTRY_USRNAME: {username}, GRAPHISTRY_PASSWORD: {password}, GRAPHISTRY_HOSTNAME: {host}, DEBUG: {debug} :)"
        ) if debug else None

        graphistry.register(
            api=api,
            protocol=protocol,
            server=host,
            username=username,
            password=password,
        )

    @typechecked
    def umap(
        self,
        X: Union[None, List[str], pd.DataFrame] = None,
        y: Union[None, str, List[str]] = None,
        render: bool = False,
        debug: bool = False,
    ) -> Union[str, HTML]:
        """umap Run UMAP on the AVR edge list, visualize in 2D, unsupervised (just X) or supervised (y).

        Parameters
        ----------
        X : Union[None, List[str]], optional
            The pd.DataFrame columns to use in the topic model, by default Non, in which case UMAP will use all columns
        y : Union[None, List[str]], optional
            The fields to supervise the clustering, by default None
        render : bool, optional
            Render a Graphistry (True) or return a URL (False), by default False
        debug : bool, optional
            Whether to log debug output, by default False

        Returns
        -------
        Union[str, HTML]
            A URL or an iframe to/with a Graphistry visualization.
        """

        if X and isinstance(X, List[str]):
            try:
                assert [x for x in X if x in self.edf.columns].all()
            except AssertionError:
                raise UMAPXColumnMissing

        if isinstance(y, str):
            y = [y]

        # Featureize the columns as text for the sentence transformer
        X_feature_cols: List[str] = [
            "Source_Port",
            "Source_IP4",
            "Source_Proto",
            "Target_Port",
            "Target_IP4",
            "Target_Proto",
            "Source_IP4_Subnet_16",
            "Source_IP4_Subnet_24",
            "Target_IP4_Subnet_16",
            "Target_IP4_Subnet_24",
            "x",
            "y",
            "specific_cluster",
            "specific_probability",
        ]
        # Feature engineering on some columns that work
        self.edf["combined_features"] = self.edf[X_feature_cols].apply(
            lambda x: " ".join(x.dropna().astype(str)), axis=1
        )

        # self.g = graphistry.nodes(self.edf).umap(X=X, y=y, **topic_model)
        # self.g = graphistry.nodes(self.edf).umap(X=X_feature_cols, y=y)
        # self.g = graphistry.nodes(self.edf).umap(
        #     X="combined_features", y=y  # , use_scaler_target="kbins", n_bins=2
        # )
        self.g = graphistry.nodes(self.edf).umap(
            X=self.edf[
                [
                    "x",
                    "y",
                    "general_cluster",
                    "specific_cluster",
                    "general_probability",
                    "specific_probability",
                ]
            ],
            y=y,
        )
        self.g = self.g.bind(point_title="ID")

        self.g = self.g.encode_point_color(
            "category",
            as_categorical=True,
            palette=categorical_palette,
            default_mapping="#CCC",
        )

        self.g = self.g.settings(
            url_params={
                "play": 1000,
                "strongGravity": True,
                "pointSize": 0.7,
                "pointOpacity": 0.6,
                "edgeOpacity": 0.3,
                "edgeCurvature": 0.4,
                "gravity": 0.75,
            }
        )

        graph_url = self.g.plot(
            render=render,
        )

        # Validate the graph_url in some data QA
        if render is False:
            assert isinstance(graph_url, str) and (len(graph_url) > 7)
            assert AVRDataResource.is_url(graph_url)

        return graph_url

    @typechecked
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
        self.g = self.g.settings(
            url_params={"play": 1000, "strongGravity": True, "pointOpacity": 0.6}
        )

        return self.g.plot(render=render)
