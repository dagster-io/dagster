import os
from datetime import datetime

import click
import dagster_graphql

from .utils import (
    LegacyQueryHistoryInfo,
    are_queries_compatible,
    deserialize_from_query_filename,
    get_queries,
    serialize_to_query_filename,
)


@click.group(
    name="query",
    help="""This cli is used for commands related to the Dagster GraphQL client's queries.
        In particular, it contains commands that pertain to checking backwards compatability.""",
)
def query():
    pass


@query.command()
def check():
    """This command checks whether backcompatability test setup is completed for the Dagster Python GraphQL Client.

    It checks if the current versions of queries in use by the GraphQL client are present in the dehydrated
    GraphQL backcompatability directory in `dagster_graphql_tests.graphql.client_backcompat.queries`

    This is useful as a reminder when new queries or added or changes are made to existing queries in
    use by the client.
    """
    current_queries_dict = get_queries()
    legacy_query_info = LegacyQueryHistoryInfo.get()

    query_directories_present = {
        query_name: query_name in legacy_query_info.legacy_queries
        for query_name in current_queries_dict
    }
    missing_query_history_subdirs = [
        query_name
        for (query_name, query_present) in query_directories_present.items()
        if not query_present
    ]
    if missing_query_history_subdirs:
        raise Exception(
            "Missing some query history (sub)directories:"
            f"\n\t{missing_query_history_subdirs}"
            + f"\n\t at {legacy_query_info.directory}"
            + "\n\t Please run `dagster-graphql-client query snapshot` on the command line "
            + "or manually resolve these issues"
        )
    for query_name in query_directories_present:
        query_dir = os.path.join(legacy_query_info.directory, query_name)
        query_is_present = False
        for filename in os.listdir(query_dir):
            file_path = os.path.join(query_dir, filename)
            with open(file_path, "r", encoding="utf8") as f:
                old_query = f.read()
                if are_queries_compatible(old_query, current_queries_dict[query_name]):
                    query_is_present = True
                    break
        if not query_is_present:
            raise Exception(
                f"The query dagster_graphql.client.client_queries.{query_name} "
                + "is not present in the backcompatability history "
                + f"directory {legacy_query_info.directory} "
                + "\n\tPlease run `dagster-graphql-client query snapshot` on the command line "
                + "or manually resolve these issues"
            )
    click.echo("All GraphQL Python Client backcompatability checks complete!")


@query.command()
def snapshot():
    """This command dehydrates the GraphQL queries used by the Dagster Python GraphQL client.

    It stores the queries as `<DAGSTER-GRAPHQL_VERSION>.<DATE>.graphql` files so that backwards compatability
    tests can be performed on the current iteration of the GraphQL queries in use.
    """
    DATE_FORMAT_STRING = "%Y_%m_%d"
    legacy_query_info = LegacyQueryHistoryInfo.get()
    for (current_query_name, current_query_body) in get_queries().items():
        query_dir = os.path.join(legacy_query_info.directory, current_query_name)
        if current_query_name not in legacy_query_info.legacy_queries:
            click.echo(
                f"Couldn't find query history subdirectory for query {current_query_name}, so making a new one"
                + f"\n\t at {query_dir}"
            )
            os.mkdir(query_dir)

        most_recent_query = None
        dagster_version_and_date_str_lst = [
            deserialize_from_query_filename(filename) for filename in os.listdir(query_dir)
        ]
        if dagster_version_and_date_str_lst:
            last_dagster_version, last_date = max(
                [
                    (dagster_version, datetime.strptime(date_str, DATE_FORMAT_STRING))
                    for (dagster_version, date_str) in dagster_version_and_date_str_lst
                ]
            )
            most_recent_query_filename = serialize_to_query_filename(
                last_dagster_version, last_date.strftime(DATE_FORMAT_STRING)
            )
            with open(os.path.join(query_dir, most_recent_query_filename), "r", encoding="utf8") as f:
                most_recent_query = f.read()

        # Create a new snapshot if it's the first one or the query is not compatible
        # with the most recent one
        if most_recent_query is None or not are_queries_compatible(
            current_query_body, most_recent_query
        ):
            query_filename = serialize_to_query_filename(
                dagster_graphql.__version__, datetime.today().strftime(DATE_FORMAT_STRING)
            )
            query_full_file_path = os.path.join(query_dir, query_filename)
            click.echo(
                f"Writing the dagster_graphql.client.client_queries.{current_query_name}"
                + f" query to a file: {query_full_file_path}"
            )
            with open(query_full_file_path, "w", encoding="utf8") as f:
                f.write(current_query_body)
    click.echo("Dagster GraphQL Client query snapshot complete!")
