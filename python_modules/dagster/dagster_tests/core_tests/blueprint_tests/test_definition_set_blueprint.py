from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pytest
from dagster import AssetKey, asset
from dagster._core.blueprints.blueprint import (
    Blueprint,
    BlueprintDefinitions,
)
from dagster._core.blueprints.definiton_set_blueprint import BlueprintDefintionSet
from dagster._core.blueprints.load_from_yaml import load_defs_from_yaml


class SimpleAssetBlueprint(Blueprint):
    key: str

    def build_defs(self) -> BlueprintDefinitions:
        @asset(key=self.key)
        def _asset(): ...

        return BlueprintDefinitions(assets=[_asset])


def test_definition_set_blueprint_from_yaml() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "definition_set_basic.yaml",
        per_file_blueprint_type=BlueprintDefintionSet[SimpleAssetBlueprint],
    )
    assert set(defs.get_asset_graph().all_asset_keys) == {
        AssetKey("asset1"),
        AssetKey("asset2"),
        AssetKey("asset3"),
    }

    for key in [AssetKey("asset1"), AssetKey("asset2"), AssetKey("asset3")]:
        assets_def = defs.get_assets_def(key)
        assert assets_def.metadata_by_key[key]["foo"] == "bar"
        assert assets_def.group_names_by_key[key] == "my_asset_group"
        assert assets_def.tags_by_key[key] == {"tag1": "value1", "tag2": "value2"}
        assert assets_def.owners_by_key[key] == ["rex@dagsterlabs.com"]
        assert assets_def.code_versions_by_key[key] == "v1"


class AdvancedAssetBlueprint(Blueprint):
    key: str
    metadata: Optional[Dict[str, Any]] = None
    group_name: Optional[str] = None
    code_version: Optional[str] = None
    owners: Optional[List[str]] = None
    tags: Optional[Dict[str, str]] = None

    def build_defs(self) -> BlueprintDefinitions:
        @asset(
            key=self.key,
            metadata=self.metadata,
            group_name=self.group_name,
            code_version=self.code_version,
            owners=self.owners,
            tags=self.tags,
        )
        def _asset(): ...

        return BlueprintDefinitions(assets=[_asset])


def test_definition_set_blueprint_override() -> None:
    # tags and metadata are appended and not replaced

    defs = (
        BlueprintDefintionSet[AdvancedAssetBlueprint](
            contents=[
                AdvancedAssetBlueprint(
                    key="asset1",
                    metadata={"foo": "bar"},
                    group_name="my_asset_group",
                    code_version="v1",
                    owners=["rex@dagsterlabs.com"],
                    tags={"tag1": "value1", "tag2": "value2"},
                ),
                AdvancedAssetBlueprint(
                    key="asset2",
                ),
            ],
            metadata={"baz": "quux"},
            tags={"tag3": "value3"},
        )
        .build_defs()
        .to_definitions()
    )

    assert set(defs.get_asset_graph().all_asset_keys) == {AssetKey("asset1"), AssetKey("asset2")}

    asset_1_key = AssetKey("asset1")
    asset_1_def = defs.get_assets_def(asset_1_key)
    assert asset_1_def.metadata_by_key[asset_1_key] == {"foo": "bar", "baz": "quux"}
    assert asset_1_def.group_names_by_key[asset_1_key] == "my_asset_group"
    assert asset_1_def.tags_by_key[asset_1_key] == {
        "tag1": "value1",
        "tag2": "value2",
        "tag3": "value3",
    }
    assert asset_1_def.owners_by_key[asset_1_key] == ["rex@dagsterlabs.com"]

    asset_2_key = AssetKey("asset2")
    asset_2_def = defs.get_assets_def(asset_2_key)
    assert asset_2_def.metadata_by_key[asset_2_key] == {"baz": "quux"}
    assert asset_2_def.group_names_by_key[asset_2_key] == "default"
    assert asset_2_def.tags_by_key[asset_2_key] == {"tag3": "value3"}
    assert asset_2_def.owners_by_key[asset_2_key] == []


def test_definition_set_nested() -> None:
    # tags and metadata are appended and not replaced

    NestedBlueprintType = BlueprintDefintionSet[
        Union["NestedBlueprintType", AdvancedAssetBlueprint]
    ]

    defs = (
        BlueprintDefintionSet(
            contents=[
                BlueprintDefintionSet(
                    contents=[
                        AdvancedAssetBlueprint(
                            key="asset1",
                        )
                    ],
                    metadata={"foo": "bar"},
                    group_name="my_asset_group",
                    code_version="v1",
                    owners=["rex@dagsterlabs.com"],
                    tags={"tag1": "value1", "tag2": "value2"},
                ),
                BlueprintDefintionSet(
                    contents=[
                        AdvancedAssetBlueprint(
                            key="asset2",
                        )
                    ],
                    metadata={"baz": "quux"},
                    group_name="my_other_asset_group",
                    code_version="v2",
                    owners=["ben@dagsterlabs.com"],
                    tags={"tag3": "value3"},
                ),
            ],
            metadata={"lorem": "ipsum"},
            tags={"tag4": "value4"},
        )
        .build_defs()
        .to_definitions()
    )

    assert set(defs.get_asset_graph().all_asset_keys) == {AssetKey("asset1"), AssetKey("asset2")}

    asset_1_key = AssetKey("asset1")
    asset_1_def = defs.get_assets_def(asset_1_key)
    assert asset_1_def.metadata_by_key[asset_1_key] == {
        "foo": "bar",
        "lorem": "ipsum",
    }
    assert asset_1_def.group_names_by_key[asset_1_key] == "my_asset_group"
    assert asset_1_def.tags_by_key[asset_1_key] == {
        "tag1": "value1",
        "tag2": "value2",
        "tag4": "value4",
    }
    assert asset_1_def.owners_by_key[asset_1_key] == ["rex@dagsterlabs.com"]

    asset_2_key = AssetKey("asset2")
    asset_2_def = defs.get_assets_def(asset_2_key)
    assert asset_2_def.metadata_by_key[asset_2_key] == {
        "baz": "quux",
        "lorem": "ipsum",
    }
    assert asset_2_def.group_names_by_key[asset_2_key] == "my_other_asset_group"
    assert asset_2_def.tags_by_key[asset_2_key] == {
        "tag3": "value3",
        "tag4": "value4",
    }
    assert asset_2_def.owners_by_key[asset_2_key] == ["ben@dagsterlabs.com"]


def test_definition_set_blueprint_override_already_set() -> None:
    with pytest.raises(Exception, match="overriding group names"):
        BlueprintDefintionSet[AdvancedAssetBlueprint](
            contents=[
                AdvancedAssetBlueprint(
                    key="asset1",
                    group_name="my_asset_group",
                ),
            ],
            group_name="my_other_asset_group",
        ).build_defs().to_definitions()

    with pytest.raises(Exception, match="overriding owners"):
        BlueprintDefintionSet[AdvancedAssetBlueprint](
            contents=[
                AdvancedAssetBlueprint(key="asset1", owners=["rex@dagsterlabs.com"]),
            ],
            owners=["ben@dagsterlabs.com"],
        ).build_defs().to_definitions()

    with pytest.raises(Exception, match="overriding code version"):
        BlueprintDefintionSet[AdvancedAssetBlueprint](
            contents=[
                AdvancedAssetBlueprint(key="asset1", code_version="v1"),
            ],
            code_version="v2",
        ).build_defs().to_definitions()
