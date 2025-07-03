from pathlib import Path

import dagster as dg
from dagster_test.components.simple_asset import SimpleAssetComponent


def test_get_component_defs_in_dagster_test() -> None:
    project_root = Path(__file__).parent.parent.parent.parent.parent / "dagster-test"
    component_defs = dg.get_all_components_defs_within_project(
        project_root=project_root,
        component_path=Path("composites/yaml"),
    )
    # type: dagster_test.components.simple_asset.SimpleAssetComponent
    # attributes:
    #   asset_key: first_yaml
    #   value: one

    # ---
    # type: dagster_test.components.simple_asset.SimpleAssetComponent
    # attributes:
    #   asset_key: second_yaml
    #   value: two
    assert len(component_defs) == 2
    assert isinstance(component_defs[0][0], SimpleAssetComponent)
    assert isinstance(component_defs[1][0], SimpleAssetComponent)
    assert component_defs[0][0].asset_key.to_user_string() == "first_yaml"
    assert component_defs[1][0].asset_key.to_user_string() == "second_yaml"
