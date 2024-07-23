from typing import Any, Mapping, Optional, Sequence

from dagster import AssetKey, external_assets_from_specs
from dagster_embedded_elt.dlt import DagsterDltTranslator, build_dlt_asset_specs
from dlt import Pipeline
from dlt.extract.resource import DltResource

from .dlt_test_sources.duckdb_with_transformer import pipeline as dlt_source


def test_with_asset_key_replacements(dlt_pipeline: Pipeline) -> None:
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_asset_key(self, resource: DltResource) -> AssetKey:
            return super().get_asset_key(resource).with_prefix("prefix")

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        assert external_asset_def.asset_deps.keys()
        assert all(key.has_prefix(["prefix"]) for key in external_asset_def.asset_deps.keys())


def test_with_deps_replacements(dlt_pipeline: Pipeline) -> None:
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_deps_asset_keys(self, _) -> Sequence[AssetKey]:
            return []

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        assert external_asset_def.asset_deps.keys()
        assert all(not deps for deps in external_asset_def.asset_deps.values())


def test_with_description_replacements(dlt_pipeline: Pipeline) -> None:
    expected_description = "customized description"

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_description(self, _) -> Optional[str]:
            return expected_description

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        for description in external_asset_def.descriptions_by_key.values():
            assert description == expected_description


def test_with_metadata_replacements(dlt_pipeline: Pipeline) -> None:
    expected_metadata = {"customized": "metadata"}

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_metadata(self, _) -> Optional[Mapping[str, Any]]:
            return expected_metadata

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        for metadata in external_asset_def.metadata_by_key.values():
            assert metadata["customized"] == "metadata"


def test_with_group_replacements(dlt_pipeline: Pipeline) -> None:
    expected_group = "customized_group"

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_group_name(self, _) -> Optional[str]:
            return expected_group

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        for group in external_asset_def.group_names_by_key.values():
            assert group == expected_group


def test_with_owner_replacements(dlt_pipeline: Pipeline) -> None:
    expected_owners = ["custom@custom.com"]

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_owners(self, _) -> Optional[Sequence[str]]:
            return expected_owners

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        for spec in external_asset_def.specs:
            assert spec.owners == expected_owners


def test_with_tag_replacements(dlt_pipeline: Pipeline) -> None:
    expected_tags = {"customized": "tag", "dagster/storage_kind": "duckdb"}

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_tags(self, _) -> Optional[Mapping[str, str]]:
            return expected_tags

    my_dlt_assets = external_assets_from_specs(
        build_dlt_asset_specs(
            dlt_source=dlt_source(),
            dlt_pipeline=dlt_pipeline,
            dagster_dlt_translator=CustomDagsterDltTranslator(),
        ),
    )

    for external_asset_def in my_dlt_assets:
        for tags in external_asset_def.tags_by_key.values():
            assert tags == expected_tags
