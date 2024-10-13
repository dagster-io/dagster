import inspect
import os
from pathlib import Path
from typing import Any, Dict

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
from dagster_dbt import DbtProject
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings

from dagster_dbt_tests.dbt_projects import test_jaffle_shop_path

JAFFLE_SHOP_ROOT_PATH = os.path.normpath(test_jaffle_shop_path)


def test_basic_attach_code_references(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_code_references=True)
        ),
        project=DbtProject(project_dir=os.fspath(test_jaffle_shop_path)),
    )
    def my_dbt_assets(): ...

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


def test_basic_attach_code_references_no_project_dir(
    test_jaffle_shop_manifest: Dict[str, Any],
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


def test_with_source_code_references_wrapper(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(enable_code_references=True)
        ),
        project=DbtProject(project_dir=os.fspath(test_jaffle_shop_path)),
    )
    def my_dbt_assets(): ...

    defs = Definitions(assets=with_source_code_references([my_dbt_assets]))

    assets = defs.get_asset_graph().all_asset_keys

    for asset_key in assets:
        asset_metadata = defs.get_assets_def(asset_key).specs_by_key[asset_key].metadata
        assert "dagster/code_references" in asset_metadata

        references = asset_metadata["dagster/code_references"].code_references
        assert len(references) == 2

        code_reference = references[1]
        assert isinstance(code_reference, LocalFileCodeReference)
        assert code_reference.file_path.endswith("test_code_references.py")


def test_link_to_git_wrapper(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
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

    assets = defs.get_asset_graph().all_asset_keys

    for asset_key in assets:
        asset_metadata = defs.get_assets_def(asset_key).specs_by_key[asset_key].metadata
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
        line_no = inspect.getsourcelines(my_dbt_assets.op.compute_fn.decorated_fn)[1]
        assert source_reference.url.endswith(f"test_code_references.py#L{line_no}")
