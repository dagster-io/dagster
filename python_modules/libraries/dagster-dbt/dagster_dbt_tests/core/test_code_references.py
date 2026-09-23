import inspect
import os
from pathlib import Path
from typing import Any

import dagster as dg
import pytest
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.source_code import (
    AnchorBasedFilePathMapping,
    LocalFileCodeReference,
    UrlCodeReference,
    link_code_references_to_git,
    with_source_code_references,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import DbtCliResource, DbtProject
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.dagster_dbt_translator import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    _attach_sql_model_code_reference,
)
from dagster_shared.record import as_dict

from dagster_dbt_tests.dbt_projects import test_jaffle_shop_path

JAFFLE_SHOP_ROOT_PATH = os.path.normpath(test_jaffle_shop_path)


def test_basic_attach_code_references(test_jaffle_shop_manifest: dict[str, Any]) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_code_references=True)
        ),
        project=DbtProject(project_dir=os.fspath(test_jaffle_shop_path)),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    for asset_key, asset_metadata in my_dbt_assets.metadata_by_key.items():
        assert "dagster/code_references" in asset_metadata

        references = asset_metadata["dagster/code_references"].code_references
        assert len(references) == 1

        reference = references[0]
        assert isinstance(reference, LocalFileCodeReference)
        assert reference.file_path.endswith(
            asset_key.path[-1] + ".sql"
        ) or reference.file_path.endswith(asset_key.path[-1] + ".csv")
        assert os.path.exists(reference.file_path), reference.file_path

    result = dg.materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))},
    )
    assert result.success


def test_basic_attach_code_references_no_project_dir(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    # expect exception because enable_code_references=True but no project_dir
    with pytest.raises(DagsterInvalidDefinitionError):

        @dbt_assets(
            manifest=test_jaffle_shop_manifest,
            dagster_dbt_translator=DagsterDbtTranslator(
                settings=DagsterDbtTranslatorSettings(enable_code_references=True)
            ),
        )
        def my_dbt_assets(): ...


def test_with_source_code_references_wrapper(test_jaffle_shop_manifest: dict[str, Any]) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_code_references=True)
        ),
        project=DbtProject(project_dir=os.fspath(test_jaffle_shop_path)),
    )
    def my_dbt_assets(): ...

    defs = Definitions(assets=with_source_code_references([my_dbt_assets]))

    assets = defs.resolve_asset_graph().get_all_asset_keys()

    for asset_key in assets:
        asset_metadata = defs.resolve_assets_def(asset_key).specs_by_key[asset_key].metadata
        assert "dagster/code_references" in asset_metadata

        references = asset_metadata["dagster/code_references"].code_references
        assert len(references) == 2

        code_reference = references[1]
        assert isinstance(code_reference, LocalFileCodeReference)
        assert code_reference.file_path.endswith("test_code_references.py")


def test_link_to_git_wrapper(test_jaffle_shop_manifest: dict[str, Any]) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_code_references=True)
        ),
        project=DbtProject(project_dir=os.fspath(test_jaffle_shop_path)),
    )
    def my_dbt_assets(): ...

    defs = Definitions(
        assets=link_code_references_to_git(
            with_source_code_references([my_dbt_assets]),
            git_url="https://github.com/dagster-io/jaffle_shop",
            git_branch="master",
            file_path_mapping=AnchorBasedFilePathMapping(
                local_file_anchor=Path(JAFFLE_SHOP_ROOT_PATH), file_anchor_path_in_repository=""
            ),
        )
    )

    assets = defs.resolve_asset_graph().get_all_asset_keys()

    for asset_key in assets:
        asset_metadata = defs.resolve_assets_def(asset_key).specs_by_key[asset_key].metadata
        assert "dagster/code_references" in asset_metadata

        references = asset_metadata["dagster/code_references"].code_references
        assert len(references) == 2

        model_reference = references[0]
        assert isinstance(model_reference, UrlCodeReference)
        assert model_reference.url.startswith(
            "https://github.com/dagster-io/jaffle_shop/tree/master/"
        )
        assert model_reference.url.endswith(
            asset_key.path[-1] + ".sql"
        ) or model_reference.url.endswith(asset_key.path[-1] + ".csv")

        source_reference = references[1]
        assert isinstance(source_reference, UrlCodeReference)
        line_no = inspect.getsourcelines(my_dbt_assets.op.compute_fn.decorated_fn)[1]  # ty: ignore[unresolved-attribute]
        assert source_reference.url.endswith(f"test_code_references.py#L{line_no}")


def test_attach_code_reference_with_string_project_dir(
    test_jaffle_shop_manifest: dict[str, Any],
) -> None:
    """Test that _attach_sql_model_code_reference works when project_dir is a string,
    as happens after serialization/deserialization through Dagster's metadata system.
    """
    # Pick a model node from the manifest that has original_file_path
    nodes = test_jaffle_shop_manifest.get("nodes", {})
    model_node = next(
        (props for props in nodes.values() if props.get("resource_type") == "model"),
        None,
    )
    assert model_node is not None, "Expected at least one model node in manifest"

    # Bypass record type checking to build the state deserialization leaves behind: a real
    # DbtProject whose project_dir is still a plain string because __new__ never coerced it.
    project = DbtProject(project_dir=os.fspath(test_jaffle_shop_path))
    project_with_str_dir = DbtProject.__nt_new__(  # ty: ignore[unresolved-attribute]
        DbtProject,
        **{**as_dict(project), "project_dir": str(test_jaffle_shop_path)},
    )
    assert isinstance(project_with_str_dir.project_dir, str)
    assert not isinstance(project_with_str_dir.project_dir, Path)

    # This would previously raise: AttributeError: 'str' object has no attribute 'joinpath'
    result = _attach_sql_model_code_reference(
        existing_metadata={},
        dbt_resource_props=model_node,
        project=project_with_str_dir,
    )

    assert "dagster/code_references" in result
    references = result["dagster/code_references"].code_references
    assert len(references) == 1
    assert isinstance(references[0], LocalFileCodeReference)
    assert os.path.exists(references[0].file_path), references[0].file_path
