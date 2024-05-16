import os
from typing import Any, Dict

from dagster._core.definitions.metadata.source_code import LocalFileCodeReference
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings

from ..dbt_projects import (
    test_jaffle_shop_path,
)


def test_basic_attach_code_references(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    @dbt_assets(
        manifest=test_jaffle_shop_manifest,
        dagster_dbt_translator=DagsterDbtTranslator(
            settings=DagsterDbtTranslatorSettings(attach_sql_model_code_reference=True)
        ),
        project_dir=os.fspath(test_jaffle_shop_path),
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
