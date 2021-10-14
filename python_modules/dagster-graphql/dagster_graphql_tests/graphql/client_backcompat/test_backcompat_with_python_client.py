import os
from typing import Iterator

import pytest
from dagster.utils import file_relative_path
from dagster_graphql.schema import create_schema
from gql import Client, gql


@pytest.fixture(scope="session", name="validator_client")
def get_validator_client() -> Client:
    return Client(schema=create_schema())


def generate_legacy_query_strings() -> Iterator[str]:
    for (dir_name, _, file_names) in os.walk(file_relative_path(__file__, "./query_snapshots")):
        for file_name in file_names:
            if file_name.endswith(".graphql"):
                with open(os.path.join(dir_name, file_name)) as f:
                    yield f.read()


@pytest.mark.parametrize("query_str", generate_legacy_query_strings())
def test_backcompat(validator_client: Client, query_str: str):
    validator_client.validate(gql(query_str))
