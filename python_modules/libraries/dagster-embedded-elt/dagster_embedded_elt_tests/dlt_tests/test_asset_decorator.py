import asyncio
from typing import Any, Mapping, Optional, Sequence

import dlt
import duckdb
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AutoMaterializePolicy,
    AutoMaterializeRule,
    Definitions,
    MonthlyPartitionsDefinition,
)
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TableSchemaMetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster_embedded_elt.dlt import DagsterDltResource, DagsterDltTranslator, dlt_assets
from dlt import Pipeline
from dlt.extract.resource import DltResource

from dagster_embedded_elt_tests.dlt_tests.dlt_test_sources.duckdb_with_transformer import (
    pipeline,
    pipeline as dlt_source,
)


def test_example_pipeline_asset_keys(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    assert {
        AssetKey("dlt_pipeline_repos"),
        AssetKey("dlt_pipeline_repo_issues"),
    } == example_pipeline_assets.keys


def test_example_pipeline_deps(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    # Since repo_issues is a transform of the repo data, its upstream
    # asset key should be the repo data asset key as well.
    assert {
        AssetKey("dlt_pipeline_repos"): {AssetKey("pipeline_repos")},
        AssetKey("dlt_pipeline_repo_issues"): {AssetKey("pipeline_repos")},
    } == example_pipeline_assets.asset_deps


def test_example_pipeline_descs(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    assert (
        example_pipeline_assets.descriptions_by_key[AssetKey("dlt_pipeline_repo_issues")]
        == "Extracted list of issues from repositories."
    )


def test_example_pipeline(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success

    temporary_duckdb_path = f"{dlt_pipeline.pipeline_name}.duckdb"
    with duckdb.connect(database=temporary_duckdb_path, read_only=True) as conn:
        row = conn.execute("select count(*) from example.repos").fetchone()
        assert row and row[0] == 3

        row = conn.execute("select count(*) from example.repo_issues").fetchone()
        assert row and row[0] == 7

    materializations = [event.materialization for event in res.get_asset_materialization_events()]
    assert all(
        "dagster/column_schema" in materialization.metadata for materialization in materializations
    )

    repos_materialization = next(
        materialization
        for materialization in materializations
        if materialization.asset_key == AssetKey("dlt_pipeline_repos")
    )
    assert repos_materialization.metadata["dagster/column_schema"] == TableSchemaMetadataValue(
        schema=TableSchema(
            columns=[
                TableColumn(name="id", type="bigint"),
                TableColumn(name="name", type="text"),
                TableColumn(name="last_modified_dt", type="text"),
                TableColumn(name="_dlt_load_id", type="text"),
                TableColumn(name="_dlt_id", type="text"),
            ]
        ),
    )


def test_multi_asset_names_do_not_conflict(dlt_pipeline: Pipeline) -> None:
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_asset_key(self, resource: DltResource) -> AssetKey:
            return AssetKey("custom_" + resource.name)

    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline, name="multi_asset_name1")
    def assets1():
        pass

    @dlt_assets(
        dlt_source=pipeline(),
        dlt_pipeline=dlt_pipeline,
        name="multi_asset_name2",
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def assets2():
        pass

    assert Definitions(assets=[assets1, assets2])


def test_get_materialize_policy(dlt_pipeline: Pipeline):
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_auto_materialize_policy(
            self, resource: DltResource
        ) -> Optional[AutoMaterializePolicy]:
            return AutoMaterializePolicy.eager().with_rules(
                AutoMaterializeRule.materialize_on_cron("0 1 * * *")
            )

    @dlt_assets(
        dlt_source=pipeline(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def assets():
        pass

    for item in assets.auto_materialize_policies_by_key.values():
        assert "0 1 * * *" in str(item)


def test_example_pipeline_has_required_metadata_keys(dlt_pipeline: Pipeline):
    required_metadata_keys = {
        "destination_type",
        "destination_name",
        "dataset_name",
        "first_run",
        "started_at",
        "finished_at",
        "jobs",
    }

    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        for asset in dlt_pipeline_resource.run(context=context):
            assert asset.metadata
            assert all(key in asset.metadata.keys() for key in required_metadata_keys)
            yield asset

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success


def test_example_pipeline_storage_kind(dlt_pipeline: Pipeline):
    for destination_type in ("duckdb", "snowflake", "bigquery"):
        destination_pipeline = dlt.pipeline(
            pipeline_name="my_test_destination",
            dataset_name="example",
            destination=destination_type,
        )

        @dlt_assets(dlt_source=pipeline(), dlt_pipeline=destination_pipeline)
        def example_pipeline_assets(
            context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
        ): ...

        for key in example_pipeline_assets.asset_and_check_keys:
            if isinstance(key, AssetKey):
                assert (
                    example_pipeline_assets.tags_by_key[key].get("dagster/storage_kind")
                    == destination_type
                )


def test_example_pipeline_subselection(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
        selection=[AssetKey(["dlt_pipeline_repo_issues"])],
    )
    assert res.success

    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 1

    found_asset_keys = [
        mat.event_specific_data.materialization.asset_key  # pyright: ignore
        for mat in asset_materializations
    ]
    assert found_asset_keys == [AssetKey(["dlt_pipeline_repo_issues"])]


def test_subset_pipeline_using_with_resources(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline().with_resources("repos"), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    assert len(example_pipeline_assets.keys) == 1
    assert example_pipeline_assets.keys == {AssetKey("dlt_pipeline_repos")}

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success

    temporary_duckdb_path = f"{dlt_pipeline.pipeline_name}.duckdb"
    with duckdb.connect(database=temporary_duckdb_path, read_only=True) as conn:
        row = conn.execute("select count(*) from example.repos").fetchone()
        assert row and row[0] == 3


def test_resource_failure_aware_materialization(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    assert len(example_pipeline_assets.keys) == 2
    assert example_pipeline_assets.keys == {
        AssetKey("dlt_pipeline_repos"),
        AssetKey("dlt_pipeline_repo_issues"),
    }

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success
    asset_materizations = res.get_asset_materialization_events()
    assert len(asset_materizations) == 2

    temporary_duckdb_path = f"{dlt_pipeline.pipeline_name}.duckdb"
    with duckdb.connect(database=temporary_duckdb_path, read_only=False) as conn:
        row = conn.execute("select count(*) from example.repos").fetchone()
        assert row and row[0] == 3
        conn.sql("drop table example.repos")

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
        raise_on_error=False,
    )
    assert not res.success
    asset_materizations = res.get_asset_materialization_events()
    assert len(asset_materizations) == 0


def test_asset_metadata(dlt_pipeline: Pipeline) -> None:
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        metadata_by_resource_name = {
            "repos": {"mode": "upsert", "primary_key": "id"},
            "repo_issues": {"mode": "upsert", "primary_key": ["repo_id", "issue_id"]},
        }

        def get_metadata(self, resource: DltResource) -> Mapping[str, Any]:
            return self.metadata_by_resource_name.get(resource.name, {})

    @dlt_assets(
        dlt_source=pipeline(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context)

    first_asset_metadata = next(iter(example_pipeline_assets.metadata_by_key.values()))
    dagster_dlt_source = first_asset_metadata.get("dagster_dlt/source")
    dagster_dlt_pipeline = first_asset_metadata.get("dagster_dlt/pipeline")
    dagster_dlt_translator = first_asset_metadata.get("dagster_dlt/translator")

    assert example_pipeline_assets.metadata_by_key == {
        AssetKey("dlt_pipeline_repos"): {
            "dagster_dlt/source": dagster_dlt_source,
            "dagster_dlt/pipeline": dagster_dlt_pipeline,
            "dagster_dlt/translator": dagster_dlt_translator,
            "mode": "upsert",
            "primary_key": "id",
        },
        AssetKey("dlt_pipeline_repo_issues"): {
            "dagster_dlt/source": dagster_dlt_source,
            "dagster_dlt/pipeline": dagster_dlt_pipeline,
            "dagster_dlt/translator": dagster_dlt_translator,
            "mode": "upsert",
            "primary_key": ["repo_id", "issue_id"],
        },
    }


def test_partitioned_materialization(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(
        dlt_source=pipeline(),
        dlt_pipeline=dlt_pipeline,
        partitions_def=MonthlyPartitionsDefinition(start_date="2022-08-09"),
    )
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        month = context.partition_key[:-3]
        yield from dlt_pipeline_resource.run(context=context, dlt_source=pipeline(month))

    async def run_partition(year: str):
        return materialize(
            [example_pipeline_assets],
            resources={"dlt_pipeline_resource": DagsterDltResource()},
            partition_key=year,
        )

    async def main():
        [res1, res2] = await asyncio.gather(
            run_partition("2022-09-01"), run_partition("2022-10-01")
        )
        assert res1.success
        assert res2.success

    asyncio.run(main())


def test_with_asset_key_replacements(dlt_pipeline: Pipeline) -> None:
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_asset_key(self, resource: DltResource) -> AssetKey:
            return super().get_asset_key(resource).with_prefix("prefix")

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    assert my_dlt_assets.asset_deps.keys()
    assert all(key.has_prefix(["prefix"]) for key in my_dlt_assets.asset_deps.keys())


def test_with_deps_replacements(dlt_pipeline: Pipeline) -> None:
    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_deps_asset_keys(self, _) -> Sequence[AssetKey]:
            return []

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    assert my_dlt_assets.asset_deps.keys()
    assert all(not deps for deps in my_dlt_assets.asset_deps.values())


def test_with_description_replacements(dlt_pipeline: Pipeline) -> None:
    expected_description = "customized description"

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_description(self, _) -> Optional[str]:
            return expected_description

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    for description in my_dlt_assets.descriptions_by_key.values():
        assert description == expected_description


def test_with_metadata_replacements(dlt_pipeline: Pipeline) -> None:
    expected_metadata = {"customized": "metadata"}

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_metadata(self, _) -> Optional[Mapping[str, Any]]:
            return expected_metadata

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    for metadata in my_dlt_assets.metadata_by_key.values():
        assert metadata["customized"] == "metadata"


def test_with_group_replacements(dlt_pipeline: Pipeline) -> None:
    expected_group = "customized_group"

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_group_name(self, _) -> Optional[str]:
            return expected_group

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    for group in my_dlt_assets.group_names_by_key.values():
        assert group == expected_group


def test_with_owner_replacements(dlt_pipeline: Pipeline) -> None:
    expected_owners = ["custom@custom.com"]

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_owners(self, _) -> Optional[Sequence[str]]:
            return expected_owners

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    for spec in my_dlt_assets.specs:
        assert spec.owners == expected_owners


def test_with_tag_replacements(dlt_pipeline: Pipeline) -> None:
    expected_tags = {"customized": "tag", "dagster/storage_kind": "duckdb"}

    class CustomDagsterDltTranslator(DagsterDltTranslator):
        def get_tags(self, _) -> Optional[Mapping[str, str]]:
            return expected_tags

    @dlt_assets(
        dlt_source=dlt_source(),
        dlt_pipeline=dlt_pipeline,
        dagster_dlt_translator=CustomDagsterDltTranslator(),
    )
    def my_dlt_assets(dlt_pipeline_resource: DagsterDltResource): ...

    for tags in my_dlt_assets.tags_by_key.values():
        assert tags == expected_tags
