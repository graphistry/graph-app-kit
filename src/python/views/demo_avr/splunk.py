import logging
import sys
from typing import Any, Dict, List

import pandas as pd
import splunklib.client as client
import splunklib.results as splunk_results
from typeguard import typechecked

# Logging is too much! Quiet it down.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.StreamHandler(sys.stderr)


class SplunkConnectException(Exception):
    """Splunk failed to connect."""

    pass


class SplunkConnection:
    """Synchronous and Asynchronous Splunk client"""

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
        self.connect()

    def connect(self) -> bool:
        try:
            self.service = client.connect(
                host=self.host, username=self.username, password=self.password
            )
            logger.debug("Splunk connection established") if self.verbose else None
            return True
        except Exception as e:
            logger.error("An exception has occurred while connection to Splunk :(")
            logger.error(e)
            raise SplunkConnectException(e)

    def get_indexes(self):
        """Returns a dictionary of index names and their fields
        This is used to provide context for the symbolic AI
        """
        indexes = {}
        logger.debug("Retrieving index information") if self.verbose else None
        for index_name in self.service.indexes:
            index = self.service.indexes[index_name.name]
            fields = index.fields
            indexes[index_name.name] = fields
        return indexes

    def get_fields(self, index: str):
        """Returns a list of fields for a given index
        This is used to provide context for the symbolic AI
        """
        logger.debug(f"Returning fields from {index}") if self.verbose else None
        query = f"search index={index} | fieldsummary | table field"
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
                    "\r%(doneProgress)03.1f%%   %(scanCount)d scanned   "
                    "%(eventCount)d matched   %(resultCount)d results"
                ) % stats

                logger.info(status)

                if stats["isDone"] == "1":
                    logger.info("\nDone!\n")
                    break

            result_count: int = stats["resultCount"]
            logger.info(f"Total results by metadata: {result_count:,}")
            offset: int = 0
            results_list: List = []

            # Doing one loop now, then another
            r = splunk_results.JSONResultsReader(
                job.results(output_mode="json", count=result_count, offset=offset)
            )

            for record in r:
                offset += 0
                results_list.append(record)
            return results_list
        except Exception as e:
            logger.error(e)
            return results_list

    def to_dataframe(self, search_query: str, *args, **kwargs) -> pd.DataFrame:
        data = list(self.query(search_query, *args, **kwargs))
        if not data:
            return pd.DataFrame()
            # is_cancelled = yield pd.DataFrame()
        logger.info(f"Found {len(data)} results.") if self.verbose else None
        df = pd.DataFrame(data)
        df.columns = [field for field in data[0].keys()]
        return df

    @typechecked
    def one_shot_splunk(
        self, query: str = 'search index="avr_59k" ', count: int = 1000
    ) -> pd.DataFrame:
        """A one-shot Splunk query that returns a pd.DataFrame"""

        reader = self.service.jobs.oneshot(
            query,
            count=count,
            earliest_time="2019-03-10T00:00:00Z",
            latest_time="2019-03-18T00:00:00Z",
            output_mode="json",
            adhoc_search_level="verbose",
        )
        splunk_results_reader = splunk_results.JSONResultsReader(reader)

        df_results = []
        for item in splunk_results_reader:
            df_results.append(item)

        df = pd.DataFrame(df_results)
        return df

    @typechecked
    @staticmethod
    def equality_query(query_dict: Dict[str, str], fields: List[str]) -> str:
        """build_query Compose a simple Splunk strink query given a query dict and field list.

        Parameters
        ----------
        query_dict : Dict[str, str]
            a field and the condition for the equivalence
        fields : List[str]
            The fields to retrieve

        Returns
        -------
        str
            Splunk query
        """
        query: str = "search "
        for col, val in query_dict.items:
            query += f"{col}={val} "
        query += " * "

        query += f' fields | {" ".join(fields)}'
