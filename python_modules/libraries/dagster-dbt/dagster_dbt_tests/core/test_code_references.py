import inspect
import os
import shutil
from pathlib import Path
from typing import Any

import dagster as dg
import pytest
from dagster import AssetKey
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
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings

from dagster_dbt_tests.dbt_projects import test_asset_checks_path, test_jaffle_shop_path

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


def test_code_references_do_not_conflict_across_distinct_project_copies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """State-backed components (e.g. several DbtProjectComponent instances scoped over one
    physical dbt project) each prepare their own local copy of the project. A source shared by
    two such components resolves to a different absolute `dagster/code_references` path per
    component even though the underlying declaration is unchanged, since the path is derived
    from each component's own project_dir. That shouldn't be treated as a real metadata conflict.
    """
    # `dbt parse` doesn't need real data, just a value for the profile's env_var() call.
    monkeypatch.setenv("DAGSTER_DBT_PYTEST_XDIST_DUCKDB_DBFILE_PATH", "unused.duckdb")
    manifest = (
        DbtCliResource(project_dir=os.fspath(test_asset_checks_path))
        .cli(["parse"])
        .wait()
        .get_artifact("manifest.json")
    )

    other_project_dir = tmp_path / "other_project_copy"
    shutil.copytree(test_asset_checks_path, other_project_dir)

    settings = DagsterDbtTranslatorSettings(enable_source_metadata=True, enable_code_references=True)

    @dbt_assets(
        manifest=manifest,
        select="stg_customers",
        dagster_dbt_translator=DagsterDbtTranslator(settings=settings),
        project=DbtProject(project_dir=os.fspath(test_asset_checks_path)),
    )
    def project_a_assets(): ...

    @dbt_assets(
        manifest=manifest,
        select="stg_customers_again",
        dagster_dbt_translator=DagsterDbtTranslator(settings=settings),
        project=DbtProject(project_dir=os.fspath(other_project_dir)),
    )
    def project_b_assets(): ...

    # Resolves without raising "Conflicting metadata found on AssetDeps", even though the two
    # components' code references point at different absolute paths for the same source.
    Definitions(assets=[project_a_assets, project_b_assets]).resolve_asset_graph()

    raw_customers_key = AssetKey(["jaffle_shop", "raw_customers"])
    checked_at_least_one_dep = False
    for assets_def in (project_a_assets, project_b_assets):
        for spec in assets_def.specs:
            for dep in spec.deps:
                if dep.asset_key == raw_customers_key:
                    checked_at_least_one_dep = True
                    # Value-stable metadata survives...
                    assert "dagster/table_name" in dep.metadata
                    assert "dagster/storage_kind" in dep.metadata
                    # ...but code references, which vary per project copy, are dropped from the
                    # dep rather than causing a conflict.
                    assert "dagster/code_references" not in dep.metadata
    assert checked_at_least_one_dep
