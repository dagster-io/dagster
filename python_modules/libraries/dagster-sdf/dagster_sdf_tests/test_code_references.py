import os
from pathlib import Path

from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.metadata.source_code import (
    LocalFileCodeReference,
    with_source_code_references,
)
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator, DagsterSdfTranslatorSettings
from dagster_sdf.sdf_workspace import SdfWorkspace

from dagster_sdf_tests.sdf_workspaces import moms_flower_shop_path


def test_basic_attach_code_references(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path,
            target_dir=moms_flower_shop_target_dir,
        ),
        dagster_sdf_translator=DagsterSdfTranslator(
            settings=DagsterSdfTranslatorSettings(enable_code_references=True)
        ),
    )
    def my_flower_shop_assets(): ...

    for asset_key, asset_metadata in my_flower_shop_assets.metadata_by_key.items():
        assert "dagster/code_references" in asset_metadata

        references = asset_metadata["dagster/code_references"].code_references
        assert len(references) == 1

        reference = references[0]
        assert isinstance(reference, LocalFileCodeReference)
        assert reference.file_path.endswith(
            asset_key.path[-1] + ".sql"
        ) or reference.file_path.endswith(asset_key.path[-1] + ".sdf.yml")
        assert os.path.exists(reference.file_path), reference.file_path


def test_basic_attach_code_references_disabled(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path,
            target_dir=moms_flower_shop_target_dir,
        ),
        dagster_sdf_translator=DagsterSdfTranslator(
            settings=DagsterSdfTranslatorSettings(enable_code_references=False)
        ),
    )
    def my_flower_shop_assets(): ...

    for asset_metadata in my_flower_shop_assets.metadata_by_key.values():
        assert "dagster/code_references" not in asset_metadata


def test_with_source_code_references_wrapper(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path,
            target_dir=moms_flower_shop_target_dir,
        ),
        dagster_sdf_translator=DagsterSdfTranslator(
            settings=DagsterSdfTranslatorSettings(enable_code_references=True)
        ),
    )
    def my_flower_shop_assets(): ...

    defs = Definitions(assets=with_source_code_references([my_flower_shop_assets]))

    assets = defs.get_asset_graph().all_asset_keys

    for asset_key in assets:
        asset_metadata = defs.get_assets_def(asset_key).specs_by_key[asset_key].metadata
        assert "dagster/code_references" in asset_metadata

        references = asset_metadata["dagster/code_references"].code_references
        assert len(references) == 2

        code_reference = references[1]
        assert isinstance(code_reference, LocalFileCodeReference)
        assert code_reference.file_path.endswith("test_code_references.py")
