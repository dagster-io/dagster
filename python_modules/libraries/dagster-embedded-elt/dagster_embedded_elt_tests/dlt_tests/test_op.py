import duckdb
from dagster import OpExecutionContext, job, op
from dagster_embedded_elt.dlt import DagsterDltResource

from .constants import EXAMPLE_PIPELINE_DUCKDB


def test_base_dlt_op(setup_dlt_pipeline) -> None:
    dlt_source, dlt_pipeline = setup_dlt_pipeline

    @op(out={})
    def my_dlt_op_yield_events(context: OpExecutionContext, dlt_resource: DagsterDltResource):
        yield from dlt_resource.run(
            context=context,
            dlt_source=dlt_source,
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

    with duckdb.connect(database=EXAMPLE_PIPELINE_DUCKDB, read_only=True) as conn:
        row = conn.execute("select count(*) from example.repos").fetchone()
        assert row and row[0] == 3

        row = conn.execute("select count(*) from example.repo_issues").fetchone()
        assert row and row[0] == 7
