from use_case_repository.guides.pipes_cli_command import cli_command_asset
from use_case_repository.guides.snowflake_to_s3_embedded_elt import (
    ingest_s3_to_snowflake,
    sling_resource,
)


def test_snowflake_to_s3_embedded_elt():
    assert ingest_s3_to_snowflake
    assert sling_resource


def test_pipes_cli_command():
    assert cli_command_asset
