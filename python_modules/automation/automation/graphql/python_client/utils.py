import os
import re
from typing import AbstractSet, NamedTuple, cast  # noqa: UP035

import dagster._check as check
import dagster_graphql_tests
from dagster_graphql.client import client_queries


class LegacyQueryHistoryInfo(NamedTuple):
    directory: str
    legacy_queries: AbstractSet[str]

    @staticmethod
    def get() -> "LegacyQueryHistoryInfo":
        directory = (
            next(iter(dagster_graphql_tests.__path__))
            + "/graphql/client_backcompat/query_snapshots"
        )
        legacy_queries = frozenset(os.listdir(directory))
        return LegacyQueryHistoryInfo(directory=directory, legacy_queries=legacy_queries)


def get_queries() -> dict[str, str]:
    """Helper function to index the graphql client's queries.

    Returns:
        Dict[str, str]: dictionary - key is variable (query) name
            the value is the query string
    """
    res_dict: dict[str, str] = {}
    for name in dir(client_queries):
        obj = getattr(client_queries, name)
        if isinstance(obj, str) and not (name.startswith("__") and name.endswith("__")):
            # remove redundant spacing from the query string
            res_dict[name] = re.sub("[\n]+", "\n", obj.strip("\n"))
    return res_dict


def are_queries_compatible(query1: str, query2: str) -> bool:
    return query1 == query2


def serialize_to_query_filename(dagster_version: str, date: str) -> str:
    return "-".join([dagster_version, date]) + ".graphql"


def deserialize_from_query_filename(query_filename: str) -> tuple[str, str]:
    parts = tuple(query_filename.rstrip(".graphql").split("-"))
    check.invariant(
        len(parts) == 2,
        f"Invalid query filename {query_filename}; must have 2 '-' separated parts.",
    )
    return cast(tuple[str, str], parts)
