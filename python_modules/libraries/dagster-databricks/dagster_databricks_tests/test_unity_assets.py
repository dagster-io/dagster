from unittest.mock import MagicMock
import types
import sys

# Stub minimal databricks modules used in unity_assets when the real SDK is not installed
databricks_mod = types.ModuleType("databricks")
sdk_mod = types.ModuleType("databricks.sdk")
service_mod = types.ModuleType("databricks.sdk.service")
catalogs_mod = types.ModuleType("databricks.sdk.service.catalogs")

class _DummyTableType:
    VIEW = "VIEW"

catalogs_mod.TableType = _DummyTableType
service_mod.catalogs = catalogs_mod
sdk_mod.WorkspaceClient = object
sys.modules.setdefault("databricks", databricks_mod)
sys.modules.setdefault("databricks.sdk", sdk_mod)
sys.modules.setdefault("databricks.sdk.service", service_mod)
sys.modules.setdefault("databricks.sdk.service.catalogs", catalogs_mod)

from dagster import AssetKey, materialize
from dagster_databricks.unity_assets import (
    unity_catalog_assets,
    databricks_job_asset,
)


class _Table:
    def __init__(self, name, schema_name, table_type="MANAGED"):
        self.name = name
        self.schema_name = schema_name
        self.table_type = table_type


class _Upstream:
    def __init__(self, catalog_name, schema_name, table_name):
        self.catalog_name = catalog_name
        self.schema_name = schema_name
        self.table_name = table_name


class _Lineage:
    def __init__(self, upstreams):
        self.upstreams = upstreams


def test_unity_catalog_assets_with_lineage():
    client = MagicMock()
    client.tables.list.return_value = [_Table("my_table", "public", "MANAGED")]
    client.lineage.get_table_lineage.return_value = _Lineage([
        _Upstream("cat", "public", "upstream")
    ])

    assets = unity_catalog_assets(client, catalog="cat", schema="public")
    assert len(assets) == 1
    spec = assets[0].get_asset_spec()
    assert spec.key == AssetKey(["cat", "public", "my_table"])
    assert AssetKey(["cat", "public", "upstream"]) in [dep.asset_key for dep in spec.deps]


def test_databricks_job_asset_executes():
    resource = MagicMock()
    resource.workspace_client.jobs.run_now.return_value = MagicMock(run_id=1, run_page_url="url")

    asset_def = databricks_job_asset(job_id=5)

    result = materialize([asset_def], resources={"databricks_client": resource})
    assert result.success
    resource.workspace_client.jobs.run_now.assert_called_with(job_id=5)
