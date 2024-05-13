from pathlib import Path
from typing import cast

import pytest
from dagster import AssetKey, AssetsDefinition, Definitions, asset, job
from dagster._core.blueprints.blueprint import Blueprint, DagsterBuildDefinitionsFromConfigError
from dagster._core.blueprints.load_from_yaml import load_defs_from_yaml
from pydantic import ValidationError


class SimpleAssetBlueprint(Blueprint):
    key: str

    def build_defs(self) -> Definitions:
        @asset(key=self.key)
        def _asset(): ...

        return Definitions(assets=[_asset])


class SimpleJobBlueprint(Blueprint):
    job_name: str

    def build_defs(self) -> Definitions:
        @job(name=self.job_name)
        def _job(): ...

        return Definitions(jobs=[_job])


def test_single_file_single_blueprint() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=SimpleAssetBlueprint,
    )
    assert len(list(defs.assets)) == 1
    assert cast(AssetsDefinition, next(iter(defs.assets))).key == AssetKey("asset1")


def test_dir_of_single_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "dir_of_single_blueprints",
        per_file_blueprint_type=SimpleAssetBlueprint,
    )
    assert len(list(defs.assets)) == 2
    assert {cast(AssetsDefinition, asset).key for asset in defs.assets} == {
        AssetKey("asset2"),
        AssetKey("asset3"),
    }


def test_abstract_blueprint() -> None:
    class AbstractAssetBlueprint(Blueprint):
        key: str

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
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

    assert "Object None is not a Definitions" in str(e.value.__cause__)


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
    assert len(list(defs.assets)) == 0


def test_model_validation_error() -> None:
    class DifferentFieldsAssetBlueprint(Blueprint):
        keykey: str

    with pytest.raises(ValidationError, match="yaml_files/single_blueprint.yaml"):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=DifferentFieldsAssetBlueprint,
        )
