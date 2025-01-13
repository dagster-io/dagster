import duckdb
from dagster import OpExecutionContext, job, op
from dagster_embedded_elt.dlt import DagsterDltResource
from dlt import Pipeline

from dagster_embedded_elt_tests.dlt_tests.dlt_test_sources.duckdb_with_transformer import pipeline


def test_base_dlt_op(dlt_pipeline: Pipeline) -> None:
    @op(out={})
    def my_dlt_op_yield_events(context: OpExecutionContext, dlt_resource: DagsterDltResource):
        yield from dlt_resource.run(
            context=context,
            dlt_source=pipeline(),
            dlt_pipeline=dlt_pipeline,
        )

    @job
    def my_dlt_op_yield_events_job() -> None:
        my_dlt_op_yield_events()

    res = my_dlt_op_yield_events_job.execute_in_process(
        resources={"dlt_resource": DagsterDltResource()}
    )

    assert res.success
    assert len(res.get_asset_materialization_events()) == 2

    duckdb_path = f"{dlt_pipeline.pipeline_name}.duckdb"
    with duckdb.connect(database=duckdb_path, read_only=True) as conn:
        row = conn.execute("select count(*) from example.repos").fetchone()
        assert row and row[0] == 3

        row = conn.execute("select count(*) from example.repo_issues").fetchone()
        assert row and row[0] == 7
