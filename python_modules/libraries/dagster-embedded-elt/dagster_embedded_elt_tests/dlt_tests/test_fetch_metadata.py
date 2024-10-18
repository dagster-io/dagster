import asyncio

import mock
from dagster import AssetExecutionContext, AssetKey, MonthlyPartitionsDefinition
from dagster._core.definitions.materialize import materialize
from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
from dlt import Pipeline

from dagster_embedded_elt_tests.dlt_tests.dlt_test_sources.duckdb_with_transformer import pipeline


def test_fetch_row_count(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        yield from dlt_pipeline_resource.run(context=context).fetch_row_count()

    res = materialize(
        [example_pipeline_assets],
        resources={"dlt_pipeline_resource": DagsterDltResource()},
    )
    assert res.success
    materializations = [event.materialization for event in res.get_asset_materialization_events()]
    assert all(
        "dagster/row_count" in materialization.metadata for materialization in materializations
    )

    repos_materialization = next(
        materialization
        for materialization in materializations
        if materialization.asset_key == AssetKey("dlt_pipeline_repos")
    )
    assert repos_materialization.metadata["dagster/row_count"].value == 3
    repo_issues_materialization = next(
        materialization
        for materialization in materializations
        if materialization.asset_key == AssetKey("dlt_pipeline_repo_issues")
    )
    assert repo_issues_materialization.metadata["dagster/row_count"].value == 7


def test_fetch_row_count_partitioned(dlt_pipeline: Pipeline) -> None:
    @dlt_assets(
        dlt_source=pipeline(),
        dlt_pipeline=dlt_pipeline,
        partitions_def=MonthlyPartitionsDefinition(start_date="2022-08-09"),
    )
    def example_pipeline_assets(
        context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
    ):
        month = context.partition_key[:-3]
        yield from dlt_pipeline_resource.run(
            context=context, dlt_source=pipeline(month)
        ).fetch_row_count()

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
        materializations1 = [
            event.materialization for event in res1.get_asset_materialization_events()
        ]
        assert all(
            "dagster/partition_row_count" in materialization.metadata
            for materialization in materializations1
        )

        repos_materialization1 = next(
            materialization
            for materialization in materializations1
            if materialization.asset_key == AssetKey("dlt_pipeline_repos")
        )
        assert repos_materialization1.metadata["dagster/partition_row_count"].value == 3

        materializations2 = [
            event.materialization for event in res2.get_asset_materialization_events()
        ]
        assert all(
            "dagster/partition_row_count" in materialization.metadata
            for materialization in materializations2
        )

        repos_materialization2 = next(
            materialization
            for materialization in materializations2
            if materialization.asset_key == AssetKey("dlt_pipeline_repos")
        )
        assert repos_materialization2.metadata["dagster/partition_row_count"].value == 0

    asyncio.run(main())


def test_fetch_row_count_failure(dlt_pipeline: Pipeline):
    with mock.patch(
        "dagster_embedded_elt.dlt.dlt_event_iterator._fetch_row_count",
        side_effect=Exception("test error"),
    ):

        @dlt_assets(dlt_source=pipeline(), dlt_pipeline=dlt_pipeline)
        def example_pipeline_assets(
            context: AssetExecutionContext, dlt_pipeline_resource: DagsterDltResource
        ):
            yield from dlt_pipeline_resource.run(context=context).fetch_row_count()

        res = materialize(
            [example_pipeline_assets],
            resources={"dlt_pipeline_resource": DagsterDltResource()},
        )

        # Assert run succeeds but no row count metadata is attached
        assert res.success
        asset_materializations = res.get_asset_materialization_events()

        metadatas = [
            asset_materialization.step_materialization_data.materialization.metadata
            for asset_materialization in asset_materializations
        ]
        assert not any(["dagster/row_count" in metadata for metadata in metadatas]), str(metadatas)
