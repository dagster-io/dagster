import pandas as pd

from snowflake_medallion.defs.resources import (
    SnowflakeResource,
)


def test_snowflake_resource_demo_mode():
    resource = SnowflakeResource(demo_mode=True)
    df = resource.query("SELECT 1")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "result" in df.columns
