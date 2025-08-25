import pytest
import yaml
from dagster.components.testing import create_defs_folder_sandbox
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksAssetBundleComponent,
)
from pydantic import ValidationError

from dagster_databricks_tests.components.databricks_asset_bundle.conftest import (
    DATABRICKS_CONFIG_LOCATION_PATH,
    TEST_DATABRICKS_WORKSPACE_HOST,
    TEST_DATABRICKS_WORKSPACE_TOKEN,
)


@pytest.mark.parametrize(
    "scaffold_params,is_successful",
    [
        ({}, False),
        (
            {
                "databricks_config_path": str(DATABRICKS_CONFIG_LOCATION_PATH),
                "databricks_workspace_host": TEST_DATABRICKS_WORKSPACE_HOST,
                "databricks_workspace_token": TEST_DATABRICKS_WORKSPACE_TOKEN,
            },
            True,
        ),
    ],
    ids=["no_params", "all_required_params"],
)
def test_scaffold_component_with_params(scaffold_params: dict, is_successful: bool):
    with create_defs_folder_sandbox() as sandbox:
        if not is_successful:
            with pytest.raises(
                ValidationError, match="validation errors for DatabricksAssetBundleScaffoldParams"
            ):
                sandbox.scaffold_component(
                    component_cls=DatabricksAssetBundleComponent,
                    scaffold_params=scaffold_params,
                )
        else:
            defs_path = sandbox.scaffold_component(
                component_cls=DatabricksAssetBundleComponent,
                scaffold_params=scaffold_params,
            )

            defs_yaml_path = defs_path / "defs.yaml"
            assert defs_yaml_path.exists()
            assert (
                str(DATABRICKS_CONFIG_LOCATION_PATH)
                in yaml.safe_load(defs_yaml_path.read_text())["attributes"][
                    "databricks_config_path"
                ]
            )
            assert {
                "host": TEST_DATABRICKS_WORKSPACE_HOST,
                "token": TEST_DATABRICKS_WORKSPACE_TOKEN,
            } == yaml.safe_load(defs_yaml_path.read_text())["attributes"]["workspace"]
