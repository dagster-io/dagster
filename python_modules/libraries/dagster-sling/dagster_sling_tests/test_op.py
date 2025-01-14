import sqlite3

from dagster import OpExecutionContext, job, op
from dagster_sling import SlingReplicationParam
from dagster_sling.resources import SlingConnectionResource, SlingResource


def test_base_sling_config_op(
    csv_to_sqlite_replication_config: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    sling_resource = SlingResource(
        connections=[
            SlingConnectionResource(type="file", name="SLING_FILE"),
            SlingConnectionResource(
                type="sqlite",
                name="SLING_SQLITE",
                connection_string=f"sqlite://{path_to_temp_sqlite_db}",
            ),
        ]
    )

    @op(out={})
    def my_sling_op_yield_events(context: OpExecutionContext, sling: SlingResource):
        yield from sling.replicate(
            context=context, replication_config=csv_to_sqlite_replication_config
        )

    @job
    def my_sling_op_yield_events_job():
        my_sling_op_yield_events()

    res = my_sling_op_yield_events_job.execute_in_process(resources={"sling": sling_resource})
    assert res.success

    assert len(res.get_asset_materialization_events()) == 1

    counts = sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0]
    assert counts == 3
