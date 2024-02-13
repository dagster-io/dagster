from docs_snippets.integrations.embedded_elt.postgres_snowflake import (
    asset_def as asset_def_postgres,
)
from docs_snippets.integrations.embedded_elt.s3_snowflake import (
    asset_def as asset_def_s3,
)


def test_asset_defs():
    assert asset_def_postgres
    assert asset_def_s3
