"""This file splunk.py implements a SplunkConnection that exposes a service and offers normal querying,
pd.DataFrames and one-shot queries. It uses environment variables from .env and is rigorously typed."""
import copy
import logging
import os
import sys
from numbers import Number
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import splunklib.client as client
import splunklib.results as splunk_results
from util import getChild

logger = getChild(__name__)

# If we are returning a DataFrame, we may not want these columns as they aren't useful and clutter the display
SPLUNK_SYSTEM_COLS = [
    "_n",
    "_bkt",
    "_raw",
    "_si",
    "_sourcetype",
    "_serial",
    "_cd",
    "_time",
    "_indextime",
    "_subsecond",
]


class SplunkConnectException(Exception):
    """Splunk failed to connect"""

    pass


class BadFilterPairException(Exception):
    """Got a bad filter pair in a non-equality query"""

    pass


class SplunkConnection:
    """Synchronous Splunk client"""

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        verbose: bool = True,
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.verbose = verbose

    def connect(self) -> bool:
        try:
            self.service = client.connect(host=self.host, username=self.username, password=self.password)
            logger.debug("Splunk connection established\n") if self.verbose else None
            return True
        except Exception as e:
            logger.error("An exception has occurred while connection to Splunk :(\n")
            logger.exception(e)
            raise SplunkConnectException(e)

    def get_indexes(self):
        """Returns a dictionary of index names and their fields
        This is used to provide context for the symbolic AI
        """
        indexes = {}
        logger.debug("Retrieving index information\n") if self.verbose else None
        for index_name in self.service.indexes:
            index = self.service.indexes[index_name.name]
            fields = index.fields
            indexes[index_name.name] = fields
        return indexes

    def get_fields(self, index: str):
        """Returns a list of fields for a given index
        This is used to provide context for the symbolic AI
        """
        logger.debug(f"Returning fields from {index}\n") if self.verbose else None
        query = f"search index={index} | fieldsummary | table field\n"
        return self.query(query)

    def query(
        self,
        search_string: str,
        earliest_time: str = None,
        latest_time: str = None,
        maxEvents: int = 30000000,
    ) -> List[Any]:
        try:
            kwargs = {"exec_mode": "normal", "count": 0}
            if earliest_time:
                kwargs["earliest_time"] = earliest_time
            if latest_time:
                kwargs["latest_time"] = latest_time

            job = self.service.jobs.create(search_string, maxEvents=maxEvents, **kwargs)
            while True:
                while not job.is_ready():
                    pass

                stats = {
                    "isDone": job["isDone"],
                    "doneProgress": float(job["doneProgress"]) * 100,
                    "scanCount": int(job["scanCount"]),
                    "eventCount": int(job["eventCount"]),
                    "resultCount": int(job["resultCount"]),
                }

                status = (
                    "\r%(doneProgress)03.1f%%   %(scanCount)d scanned   " "%(eventCount)d matched   %(resultCount)d results\n"
                ) % stats

                logger.info(status)

                if stats["isDone"] == "1":
                    logger.info("Query done!\n")
                    break

            result_count: int = stats["resultCount"]
            logger.info(f"Total results by metadata: {result_count:,}\n")
            offset: int = 0
            results_list: List = []

            # Doing one loop now, then another
            r = splunk_results.JSONResultsReader(job.results(output_mode="json", count=result_count, offset=offset))

            for record in r:
                offset += 0
                results_list.append(record)
            return results_list
        except Exception as e:
            logger.error("Exception querying data :(\n")
            logger.error(e)
            return results_list

    def to_dataframe(self, search_query: str, *args, **kwargs) -> pd.DataFrame:
        data = list(self.query(search_query, *args, **kwargs))
        if not data:
            return pd.DataFrame()
            # is_cancelled = yield pd.DataFrame()
        logger.info(f"Found {len(data)} results.\n") if self.verbose else None
        df: pd.DataFrame = pd.DataFrame.from_dict(data)
        df.columns = [field for field in data[0].keys()]
        return df

    def one_shot_splunk(
        self,
        query: str,
        drop_cols: Optional[List[str]] = SPLUNK_SYSTEM_COLS,
        count: int = 1000,
    ) -> pd.DataFrame:
        """A one-shot Splunk query that returns a pd.DataFrame"""

        reader = self.service.jobs.oneshot(
            query,
            count=count,
            output_mode="json",
            adhoc_search_level="verbose",
        )
        splunk_results_reader = splunk_results.JSONResultsReader(reader)

        df_results: List[Dict[str, Any]] = []
        for item in splunk_results_reader:
            # Skip any Messages we recieve, like telling us we are receiving partial results
            if isinstance(item, splunk_results.Message):
                logger.info(f"splunk.results.Message received: {item}\n")
                continue

            # We don't want to alter an item while we are iterating it
            cleaned_item = copy.copy(item)

            # For now we do not need the values of the dropped fields
            if drop_cols and isinstance(drop_cols, list):
                [cleaned_item.pop(field) for field in drop_cols if field in cleaned_item]

            # Put the cleaned up item in the list that will become a pd.DataFrame
            df_results.append(cleaned_item)

        df: pd.DataFrame = pd.DataFrame.from_dict(df_results)
        return df

    @staticmethod
    def parse_filter_pair(query: str, col: str, filter_pair: Tuple[str, Union[str, int, float]]) -> str:
        # First comes op, then comes value
        op = filter_pair[0]
        value = filter_pair[1]

        filter_query = ""

        # Have to validate tuples for non-equality queries
        if op and isinstance(op, str) and (op not in ("None", "")):
            # If the value isn't a None alias, then build the query string
            if value and (str(value) not in "None", ""):
                # ex.      "col  >=  value"
                filter_query += f"{col}{op}{value} "
            else:
                logger.error(f"Invalid value for filter pair: {value}\n")
                raise BadFilterPairException(f"Invalid value for filter pair: {value}")

        # If the operator isn't a string - abandon hope
        else:
            logger.error(f"Invalid operater in filter pair: {op}\n")
            raise BadFilterPairException(f"Invalid operater in filter pair: {op}")

        return filter_query

    @staticmethod
    def build_query(
        index: str,
        query_dict: Optional[
            Dict[
                str,
                Union[
                    str,
                    int,
                    float,
                    Tuple[str, Union[str, Number]],
                    List[Tuple[str, Union[str, Number]]],
                ],
            ]
        ] = None,
        fields: Optional[List[str]] = None,
        sort: Optional[List[str]] = None,
        debug: bool = False,
    ) -> str:
        """build_query Compose a simple Splunk strink query given a query dict and field list.

        Parameters
        ----------
        index: str
            The index to search
        query_dict : Optional[Dict[str, Union[str, int, float, Tuple[str]]]]
            A field and the value to match. Value can also be a 2-list of the format: (operator, value)
        fields : Optional[List[str]]
            The fields to retrieve, by default None. It can help to list these or they might not be retrieved.
        sort: Optional[List[str]]
            The fields to sort by, by default [_bkt, _cnt] to get a deterministic sort to make queries reproducible.

        Returns
        -------
        str
            String Splunk query
        """
        query: str = f'search index="{index}" '
        for col, val in query_dict.items():
            if val and (val not in ("None", "")):
                # Non-equality query
                if isinstance(val, Tuple) or isinstance(val, List):
                    # If it is a nested list, there is more than one condition
                    if len(val) > 0 and isinstance(val[0], Tuple):
                        for filter_pair in val:
                            assert len(filter_pair) == 2
                            try:
                                query += SplunkConnection.parse_filter_pair(query=query, col=col, filter_pair=filter_pair)
                            except BadFilterPairException:
                                continue

                    # This is a single conditional query
                    else:
                        assert len(val) == 2
                        try:
                            query += SplunkConnection.parse_filter_pair(query=query, col=col, filter_pair=val)
                        except BadFilterPairException:
                            continue

                # Default equals
                else:
                    query += f"{col}={val} "

        # Add any fields listed in the table command - without fields queries can get flaky
        query += f'| table {" ".join(fields)} ' if fields else ""

        # Default random sort - otherwise must be deterministic
        if sort and isinstance(sort, list) and len(list) > 0:
            query += f'| sort {" ".join(sort)} ' if sort else ""
        else:
            query += "| eval _random=random() | sort 0 _random"

        if debug:
            logger.debug(f"Splunk query: {query}\n")

        return query

    def get_unique_values(self, index: str, field: str) -> List[Optional[Union[str, Number]]]:
        """get_unique_values Get the unique values of any field in any index using Splunk's stats command

        Parameters
        ----------
        index : str
            Splunk index to query
        field : str
            Field from which to seek unique values

        Returns
        -------
        List[str]
            List of unique values for a field in an index
        """
        query = f'search index="{index}" | fields {field} | dedup {field} | sort +num({field})'

        unique_df = self.one_shot_splunk(query, drop_cols=None)
        unique_vals = unique_df[field].drop_duplicates().tolist()

        return unique_vals
