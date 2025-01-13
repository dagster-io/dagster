from docs_snippets.integrations.sling.postgres_snowflake import (
    my_assets as asset_def_postgres,
)
from docs_snippets.integrations.sling.s3_snowflake import my_assets as asset_def_s3
from docs_snippets.integrations.sling.sling_connection_resources import sling_resource


def test_asset_defs() -> None:
    assert asset_def_postgres
    assert asset_def_s3
    assert sling_resource
