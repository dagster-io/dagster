import pandas as pd

from databricks_delta.defs.resources import (  # type: ignore[import-not-found]
    DatabricksResource,
    DeltaStorageResource,
)


def test_databricks_resource_demo_mode():
    resource = DatabricksResource(demo_mode=True)
    df = resource.query("SELECT 1")
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_delta_storage_resource_demo_mode():
    resource = DeltaStorageResource(storage_path="data/delta", demo_mode=True)
    path = resource.write_delta_table("test", pd.DataFrame())
    assert path == "data/delta/test"


def test_delta_storage_read_demo_mode():
    resource = DeltaStorageResource(storage_path="data/delta", demo_mode=True)
    df = resource.read_delta_table("test")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
