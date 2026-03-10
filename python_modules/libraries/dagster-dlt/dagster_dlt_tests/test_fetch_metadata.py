import asyncio
from unittest import mock

from dagster import AssetExecutionContext, AssetKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.partitions.definition import MonthlyPartitionsDefinition
from dagster_dlt import DagsterDltResource, dlt_assets
from dlt import Pipeline

from dagster_dlt_tests.dlt_test_sources.duckdb_with_transformer import pipeline


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
        "dagster_dlt.dlt_event_iterator._fetch_row_count",
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


def test_fetch_row_count_no_jobs():
    """Test that fetch_row_count_metadata handles empty jobs list gracefully.

    When a dlt source yields no data, the jobs metadata may be an empty list.
    Instead of raising an exception, we should return TableMetadataSet with row_count=None.
    Regression test for https://github.com/dagster-io/dagster/issues/33572
    """
    from dagster import AssetMaterialization
    from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
    from dagster_dlt.dlt_event_iterator import fetch_row_count_metadata

    # Test with empty jobs list
    materialization = AssetMaterialization(
        asset_key="test_asset",
        metadata={"jobs": []},
    )

    context = mock.MagicMock()
    context.has_partition_key = False
    dlt_pipeline_mock = mock.MagicMock()

    result = fetch_row_count_metadata(materialization, context, dlt_pipeline_mock)
    assert isinstance(result, TableMetadataSet)
    assert result.row_count is None
    context.log.debug.assert_called_once()
    context.log.debug.reset_mock()

    # Test with missing jobs key entirely
    materialization_no_jobs = AssetMaterialization(
        asset_key="test_asset",
        metadata={"some_other_key": "value"},
    )

    result_no_jobs = fetch_row_count_metadata(materialization_no_jobs, context, dlt_pipeline_mock)
    assert isinstance(result_no_jobs, TableMetadataSet)
    assert result_no_jobs.row_count is None


def test_extract_resource_metadata_no_normalize_info():
    """Test that extract_resource_metadata handles None last_normalize_info gracefully.

    When a dlt source yields no data, dlt skips the normalize step and
    last_normalize_info returns None. The metadata extraction should still
    succeed without rows_loaded in the output.
    Regression test for https://github.com/dagster-io/dagster/issues/33572
    """
    from dagster_dlt.resource import DagsterDltResource

    dagster_dlt_resource = DagsterDltResource()

    # Mock context
    context = mock.MagicMock()

    # Mock dlt resource
    dlt_resource = mock.MagicMock()
    dlt_resource.table_name = "test_table"

    # Mock load_info with minimal valid data
    load_info = mock.MagicMock()
    load_info.asdict.return_value = {
        "first_run": True,
        "started_at": "2024-01-01",
        "finished_at": "2024-01-01",
        "dataset_name": "test",
        "destination_name": "duckdb",
        "destination_type": "duckdb",
        "load_packages": [],
    }

    # Mock dlt_pipeline with last_trace.last_normalize_info = None
    dlt_pipeline_mock = mock.MagicMock()
    dlt_pipeline_mock.last_trace.last_normalize_info = None
    dlt_pipeline_mock.default_schema.naming.normalize_table_identifier.return_value = "test_table"
    dlt_pipeline_mock.default_schema.data_table_names.return_value = []
    dlt_pipeline_mock.default_schema.get_table_columns.return_value = {}

    metadata = dagster_dlt_resource.extract_resource_metadata(
        context, dlt_resource, load_info, dlt_pipeline_mock
    )

    # Should succeed without crashing
    assert "rows_loaded" not in metadata


def test_extract_resource_metadata_no_last_trace():
    """Test that extract_resource_metadata handles None last_trace gracefully.

    Defensive guard: if last_trace itself is None, metadata extraction should
    still succeed without rows_loaded.
    Regression test for https://github.com/dagster-io/dagster/issues/33572
    """
    from dagster_dlt.resource import DagsterDltResource

    dagster_dlt_resource = DagsterDltResource()

    context = mock.MagicMock()
    dlt_resource = mock.MagicMock()
    dlt_resource.table_name = "test_table"

    load_info = mock.MagicMock()
    load_info.asdict.return_value = {
        "first_run": True,
        "started_at": "2024-01-01",
        "finished_at": "2024-01-01",
        "dataset_name": "test",
        "destination_name": "duckdb",
        "destination_type": "duckdb",
        "load_packages": [],
    }

    # Mock dlt_pipeline with last_trace = None
    dlt_pipeline_mock = mock.MagicMock()
    dlt_pipeline_mock.last_trace = None
    dlt_pipeline_mock.default_schema.naming.normalize_table_identifier.return_value = "test_table"
    dlt_pipeline_mock.default_schema.data_table_names.return_value = []
    dlt_pipeline_mock.default_schema.get_table_columns.return_value = {}

    metadata = dagster_dlt_resource.extract_resource_metadata(
        context, dlt_resource, load_info, dlt_pipeline_mock
    )

    assert "rows_loaded" not in metadata
