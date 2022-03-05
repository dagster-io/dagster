# pylint: disable=print-call
"""
A basic script that will create tables in the source postgres database, then automatically
create an Airbyte Connection between the source database and destination database.
"""
# pylint: disable=print-call
import random

import numpy as np
import pandas as pd
from dagster_airbyte import AirbyteResource
from dagster_postgres.utils import get_conn_string

from dagster import check

from .constants import PG_DESTINATION_CONFIG, PG_SOURCE_CONFIG

# configures the number of records for each table
N_USERS = 100
N_ORDERS = 10000


def _create_ab_source(client: AirbyteResource) -> str:
    workspace_id = client.make_request("/workspaces/list", data={})["workspaces"][0]["workspaceId"]

    # get latest available Postgres source definition
    source_defs = client.make_request(
        "/source_definitions/list_latest", data={"workspaceId": workspace_id}
    )
    postgres_definitions = [
        sd for sd in source_defs["sourceDefinitions"] if sd["name"] == "Postgres"
    ]
    if not postgres_definitions:
        raise check.CheckError("Expected at least one Postgres source definition.")
    source_definition_id = postgres_definitions[0]["sourceDefinitionId"]

    # create Postgres source
    source_id = client.make_request(
        "/sources/create",
        data={
            "sourceDefinitionId": source_definition_id,
            "connectionConfiguration": dict(**PG_SOURCE_CONFIG, ssl=False),
            "workspaceId": workspace_id,
            "name": "Source Database",
        },
    )["sourceId"]
    print(f"Created Airbyte Source: {source_id}")
    return source_id


def _create_ab_destination(client: AirbyteResource) -> str:
    workspace_id = client.make_request("/workspaces/list", data={})["workspaces"][0]["workspaceId"]

    # get the latest available Postgres destination definition
    destination_defs = client.make_request(
        "/destination_definitions/list_latest", data={"workspaceId": workspace_id}
    )
    postgres_definitions = [
        dd for dd in destination_defs["destinationDefinitions"] if dd["name"] == "Postgres"
    ]
    if not postgres_definitions:
        raise check.CheckError("Expected at least one Postgres destination definition.")
    destination_definition_id = postgres_definitions[0]["destinationDefinitionId"]

    # create Postgres destination
    destination_id = client.make_request(
        "/destinations/create",
        data={
            "destinationDefinitionId": destination_definition_id,
            "connectionConfiguration": dict(**PG_DESTINATION_CONFIG, schema="public", ssl=False),
            "workspaceId": workspace_id,
            "name": "Destination Database",
        },
    )["destinationId"]
    print(f"Created Airbyte Destination: {destination_id}")
    return destination_id


def setup_airbyte():
    client = AirbyteResource(host="localhost", port="8000", use_https=False)
    source_id = _create_ab_source(client)
    destination_id = _create_ab_destination(client)

    source_catalog = client.make_request("/sources/discover_schema", data={"sourceId": source_id})[
        "catalog"
    ]

    # create a connection between the new source and destination
    connection_id = client.make_request(
        "/connections/create",
        data={
            "name": "Example Connection",
            "sourceId": source_id,
            "destinationId": destination_id,
            "syncCatalog": source_catalog,
            "prefix": "",
            "status": "active",
        },
    )["connectionId"]

    print(f"Created Airbyte Connection: {connection_id}")


def _random_dates():

    start = pd.to_datetime("2021-01-01")
    end = pd.to_datetime("2022-01-01")

    start_u = start.value // 10**9
    end_u = end.value // 10**9

    dist = np.random.standard_exponential(size=N_ORDERS) / 10

    clipped_flipped_dist = 1 - dist[dist <= 1]
    clipped_flipped_dist = clipped_flipped_dist[:-1]

    if len(clipped_flipped_dist) < N_ORDERS:
        clipped_flipped_dist = np.append(
            clipped_flipped_dist, clipped_flipped_dist[: N_ORDERS - len(clipped_flipped_dist)]
        )

    return pd.to_datetime((clipped_flipped_dist * (end_u - start_u)) + start_u, unit="s")


def add_data():
    con_string = get_conn_string(
        username=PG_SOURCE_CONFIG["username"],
        password=PG_SOURCE_CONFIG["password"],
        hostname=PG_SOURCE_CONFIG["host"],
        port=str(PG_SOURCE_CONFIG["port"]),
        db_name=PG_SOURCE_CONFIG["database"],
    )

    users = pd.DataFrame(
        {
            "user_id": range(N_USERS),
            "is_bot": [random.choice([True, False]) for _ in range(N_USERS)],
        }
    )

    users.to_sql("users", con=con_string, if_exists="replace")
    print("Created users table.")

    orders = pd.DataFrame(
        {
            "user_id": [random.randint(0, N_USERS) for _ in range(N_ORDERS)],
            "order_time": _random_dates(),
            "order_value": np.random.normal(loc=100.0, scale=15.0, size=N_ORDERS),
        }
    )

    orders.to_sql("orders", con=con_string, if_exists="replace")
    print("Created orders table.")


add_data()
setup_airbyte()
