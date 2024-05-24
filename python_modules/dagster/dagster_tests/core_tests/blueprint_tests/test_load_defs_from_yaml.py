from pathlib import Path
from typing import Literal, Union

import pytest
from dagster import AssetKey, asset, job
from dagster._core.blueprints.blueprint import (
    Blueprint,
    BlueprintDefinitions,
    DagsterBuildDefinitionsFromConfigError,
)
from dagster._core.blueprints.load_from_yaml import load_defs_from_yaml
from dagster._model.pydantic_compat_layer import USING_PYDANTIC_1
from pydantic import ValidationError


class SimpleAssetBlueprint(Blueprint):
    key: str

    def build_defs(self) -> BlueprintDefinitions:
        @asset(key=self.key)
        def _asset(): ...

        return BlueprintDefinitions(assets=[_asset])


class SimpleJobBlueprint(Blueprint):
    job_name: str

    def build_defs(self) -> BlueprintDefinitions:
        @job(name=self.job_name)
        def _job(): ...

        return BlueprintDefinitions(jobs=[_job])


def test_single_file_single_blueprint() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=SimpleAssetBlueprint,
    )
    assert set(defs.get_asset_graph().all_asset_keys) == {AssetKey("asset1")}


def test_dir_of_single_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "dir_of_single_blueprints",
        per_file_blueprint_type=SimpleAssetBlueprint,
    )
    assert set(defs.get_asset_graph().all_asset_keys) == {AssetKey("asset2"), AssetKey("asset3")}


def test_abstract_blueprint() -> None:
    class AbstractAssetBlueprint(Blueprint):
        key: str

    with pytest.raises(Exception, match="Can't instantiate abstract class"):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=AbstractAssetBlueprint,
        )


def test_build_defs_returns_none() -> None:
    class ReturnsNoneAssetBlueprint(Blueprint):
        key: str

        def build_defs(self):
            return None

    with pytest.raises(
        DagsterBuildDefinitionsFromConfigError, match="yaml_files/single_blueprint.yaml"
    ) as e:
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=ReturnsNoneAssetBlueprint,
        )

    assert "Object None is not a BlueprintDefinitions" in str(e.value.__cause__)


def test_build_defs_raises_error() -> None:
    class ErroringAssetBlueprint(Blueprint):
        key: str

        def build_defs(self):
            raise RuntimeError("glog")

    with pytest.raises(
        DagsterBuildDefinitionsFromConfigError, match="yaml_files/single_blueprint.yaml"
    ) as e:
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=ErroringAssetBlueprint,
        )

    assert "glog" in str(e.value.__cause__)


def test_file_doesnt_exist() -> None:
    with pytest.raises(Exception, match="No file or directory at path"):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "nonexistent_file.yaml",
            per_file_blueprint_type=SimpleAssetBlueprint,
        )


def test_empty_dir() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "dir_with_no_yaml_files",
        per_file_blueprint_type=SimpleAssetBlueprint,
    )
    assert len(set(defs.get_asset_graph().all_asset_keys)) == 0


def test_model_validation_error() -> None:
    class DifferentFieldsAssetBlueprint(Blueprint):
        keykey: str

    match = "" if USING_PYDANTIC_1 else "yaml_files/single_blueprint.yaml"
    with pytest.raises(ValidationError, match=match):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=DifferentFieldsAssetBlueprint,
        )


def test_single_file_union_of_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=Union[SimpleAssetBlueprint, SimpleJobBlueprint],
    )
    assert set(defs.get_asset_graph().all_asset_keys) == {AssetKey("asset1")}


def test_single_file_union_of_blueprints_discriminated_union() -> None:
    class SameFieldsAssetBlueprint1(Blueprint):
        type: Literal["type1"]
        key: str

        def build_defs(self) -> BlueprintDefinitions:
            assert False, "shouldn't get here"

    class SameFieldsAssetBlueprint2(Blueprint):
        type: Literal["type2"]
        key: str

        def build_defs(self) -> BlueprintDefinitions:
            @asset(key=self.key)
            def _asset(): ...

            return BlueprintDefinitions(assets=[_asset])

    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint_with_type.yaml",
        per_file_blueprint_type=Union[SameFieldsAssetBlueprint1, SameFieldsAssetBlueprint2],
    )
    assert set(defs.get_asset_graph().all_asset_keys) == {AssetKey("asset1")}
