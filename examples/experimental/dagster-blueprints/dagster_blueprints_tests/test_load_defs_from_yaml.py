import os
import sys
from pathlib import Path
from typing import List, Literal, Sequence, Union

import pytest
from dagster import AssetKey, Definitions, asset, job
from dagster._check import CheckError
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    LocalFileCodeReference,
)
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster_blueprints.blueprint import Blueprint, DagsterBuildDefinitionsFromConfigError
from dagster_blueprints.load_from_yaml import YamlBlueprintsLoader, load_defs_from_yaml
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
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {AssetKey("asset1")}

    metadata = defs.get_assets_def("asset1").metadata_by_key[AssetKey("asset1")]
    code_references_metadata = CodeReferencesMetadataSet.extract(metadata)
    assert code_references_metadata.code_references
    assert len(code_references_metadata.code_references.code_references) == 1
    reference = code_references_metadata.code_references.code_references[0]
    assert isinstance(reference, LocalFileCodeReference)
    assert reference.file_path == os.fspath(
        Path(__file__).parent / "yaml_files" / "single_blueprint.yaml"
    )
    assert reference.line_number == 1


def test_dir_of_single_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "dir_of_single_blueprints",
        per_file_blueprint_type=SimpleAssetBlueprint,
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey("asset2"),
        AssetKey("asset3"),
    }

    for asset_key, expected_filename in (
        (AssetKey("asset2"), "single_blueprint1.yaml"),
        (AssetKey("asset3"), "single_blueprint2.yaml"),
    ):
        metadata = defs.get_assets_def(asset_key).metadata_by_key[asset_key]
        code_references_metadata = CodeReferencesMetadataSet.extract(metadata)
        assert code_references_metadata.code_references
        assert len(code_references_metadata.code_references.code_references) == 1
        reference = code_references_metadata.code_references.code_references[0]
        assert isinstance(reference, LocalFileCodeReference)
        assert reference.file_path == os.fspath(
            Path(__file__).parent / "yaml_files" / "dir_of_single_blueprints" / expected_filename
        )
        assert reference.line_number == 1


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
    assert len(set(defs.get_asset_graph().get_all_asset_keys())) == 0


def test_model_validation_error() -> None:
    class DifferentFieldsAssetBlueprint(Blueprint):
        keykey: str

    with pytest.raises(ValidationError, match="yaml_files/single_blueprint.yaml"):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=DifferentFieldsAssetBlueprint,
        )


def test_single_file_union_of_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=Union[SimpleAssetBlueprint, SimpleJobBlueprint],
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {AssetKey("asset1")}


def test_single_file_union_of_blueprints_discriminated_union() -> None:
    class SameFieldsAssetBlueprint1(Blueprint):
        type: Literal["type1"]
        key: str

        def build_defs(self) -> Definitions:
            assert False, "shouldn't get here"

    class SameFieldsAssetBlueprint2(Blueprint):
        type: Literal["type2"]
        key: str

        def build_defs(self) -> Definitions:
            @asset(key=self.key)
            def _asset(): ...

            return Definitions(assets=[_asset])

    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint_with_type.yaml",
        per_file_blueprint_type=Union[SameFieldsAssetBlueprint1, SameFieldsAssetBlueprint2],
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {AssetKey("asset1")}


class SourceFileNameAssetBlueprint(Blueprint):
    key: str

    def build_defs(self) -> Definitions:
        @asset(key=self.key, metadata={"source_file_name": self.source_file_name})
        def _asset(): ...

        return Definitions(assets=[_asset])


def test_source_file_name() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=SourceFileNameAssetBlueprint,
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {AssetKey("asset1")}

    metadata = defs.get_assets_def("asset1").metadata_by_key[AssetKey("asset1")]
    assert metadata["source_file_name"] == "single_blueprint.yaml"


class SimpleAssetBlueprintNeedsResource(Blueprint):
    key: str

    def build_defs(self) -> Definitions:
        @asset(key=self.key, required_resource_keys={"some_resource"})
        def _asset(): ...

        return Definitions(assets=[_asset])


def test_additional_resources() -> None:
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'some_resource' required by op 'asset1' was not provided",
    ):
        Definitions.validate_loadable(
            load_defs_from_yaml(
                path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
                per_file_blueprint_type=SimpleAssetBlueprintNeedsResource,
            )
        )

    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=SimpleAssetBlueprintNeedsResource,
        resources={"some_resource": "some_value"},
    )

    assert set(defs.get_asset_graph().get_all_asset_keys()) == {AssetKey("asset1")}


def test_yaml_blueprints_loader_additional_resources() -> None:
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'some_resource' required by op 'asset1' was not provided",
    ):
        Definitions.validate_loadable(
            YamlBlueprintsLoader(
                path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
                per_file_blueprint_type=SimpleAssetBlueprintNeedsResource,
            ).load_defs()
        )

    defs = YamlBlueprintsLoader(
        path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
        per_file_blueprint_type=SimpleAssetBlueprintNeedsResource,
    ).load_defs(resources={"some_resource": "some_value"})

    assert set(defs.get_asset_graph().get_all_asset_keys()) == {AssetKey("asset1")}


def test_loader_schema(snapshot) -> None:
    class SimpleAssetBlueprint(Blueprint):
        key: str

    loader = YamlBlueprintsLoader(path=Path(__file__), per_file_blueprint_type=SimpleAssetBlueprint)

    model_schema = loader.model_json_schema()
    snapshot.assert_match(model_schema)

    if model_schema["title"] == "ParsingModel[SimpleAssetBlueprint]":
        assert model_schema["$ref"] == "#/definitions/SimpleAssetBlueprint"
        model_schema = model_schema["definitions"]["SimpleAssetBlueprint"]

    assert model_schema["title"] == "SimpleAssetBlueprint"
    assert model_schema["type"] == "object"
    model_keys = model_schema["properties"].keys()
    assert set(model_keys) == {"key"}


def test_loader_schema_sequence(snapshot) -> None:
    class SimpleAssetBlueprint(Blueprint):
        key: str

    loader = YamlBlueprintsLoader(
        path=Path(__file__), per_file_blueprint_type=Sequence[SimpleAssetBlueprint]
    )

    model_schema = loader.model_json_schema()
    snapshot.assert_match(model_schema)

    assert model_schema["type"] == "array"


def test_loader_schema_union(snapshot) -> None:
    class FooAssetBlueprint(Blueprint):
        type: Literal["foo"] = "foo"
        number: int

    class BarAssetBlueprint(Blueprint):
        type: Literal["bar"] = "bar"
        string: str

    loader = YamlBlueprintsLoader(
        path=Path(__file__), per_file_blueprint_type=Union[FooAssetBlueprint, BarAssetBlueprint]
    )

    model_schema = loader.model_json_schema()
    snapshot.assert_match(model_schema)

    # Pydantic 1 uses $ref, Pydantic 2 uses #ref
    # Just make sure the top-level union object points to both blueprints
    assert len(model_schema["anyOf"]) == 2
    any_of_refs = [
        item.get("#ref", item.get("$ref")).split("/")[-1] for item in model_schema["anyOf"]
    ]
    assert set(any_of_refs) == {"FooAssetBlueprint", "BarAssetBlueprint"}


def test_single_file_many_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "list_of_blueprints.yaml",
        per_file_blueprint_type=list[SimpleAssetBlueprint],
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey("asset1"),
        AssetKey("asset2"),
        AssetKey("asset3"),
    }

    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "list_of_blueprints.yaml",
        per_file_blueprint_type=Sequence[SimpleAssetBlueprint],
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey("asset1"),
        AssetKey("asset2"),
        AssetKey("asset3"),
    }


# Disabled for Python versions <3.9 as builtin types do not support generics
# until Python 3.9, https://peps.python.org/pep-0585/
@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9")
def test_single_file_many_blueprints_builtin_list() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "list_of_blueprints.yaml",
        per_file_blueprint_type=list[SimpleAssetBlueprint],
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey("asset1"),
        AssetKey("asset2"),
        AssetKey("asset3"),
    }


def test_single_file_no_bp_type() -> None:
    with pytest.raises(
        CheckError, match="Sequence type annotation must have a single Blueprint type argument"
    ):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "list_of_blueprints.yaml",
            per_file_blueprint_type=list,
        )
    with pytest.raises(
        CheckError, match="Sequence type annotation must have a single Blueprint type argument"
    ):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "list_of_blueprints.yaml",
            per_file_blueprint_type=Sequence,
        )


def test_expect_list_no_list() -> None:
    with pytest.raises(
        DagsterInvariantViolationError, match="Expected a list of objects at document root, but got"
    ):
        load_defs_from_yaml(
            path=Path(__file__).parent / "yaml_files" / "single_blueprint.yaml",
            per_file_blueprint_type=list[SimpleAssetBlueprint],
        )


def test_dir_of_many_blueprints() -> None:
    defs = load_defs_from_yaml(
        path=Path(__file__).parent / "yaml_files" / "dir_of_lists_of_blueprints",
        per_file_blueprint_type=list[SimpleAssetBlueprint],
    )
    assert set(defs.get_asset_graph().get_all_asset_keys()) == {
        AssetKey("asset1"),
        AssetKey("asset2"),
        AssetKey("asset3"),
        AssetKey("asset4"),
    }
