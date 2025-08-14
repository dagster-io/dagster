import pytest
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
)


@pytest.mark.parametrize(
    "scaffold_params",
    [
        {},
    ],
    ids=["no_params"],
)
def test_scaffold_component_with_params(scaffold_params: dict):
    with create_defs_folder_sandbox() as sandbox:
        with pytest.raises(NotImplementedError):
            sandbox.scaffold_component(
                component_cls=DatabricksAssetBundleComponent,
                scaffold_params=scaffold_params,
            )
