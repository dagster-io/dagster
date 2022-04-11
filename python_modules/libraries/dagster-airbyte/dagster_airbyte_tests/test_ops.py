import responses
from dagster_airbyte import AirbyteOutput, airbyte_resource, airbyte_sync_op

from dagster import job, op

DEFAULT_CONNECTION_ID = "02087b3c-2037-4db9-ae7b-4a8e45dc20b1"


def test_airbyte_sync_op():

    ab_host = "some_host"
    ab_port = "8000"
    ab_url = f"http://{ab_host}:{ab_port}/api/v1"
    ab_resource = airbyte_resource.configured({"host": ab_host, "port": ab_port})

    @op
    def foo_op():
        pass

    @job(
        resource_defs={"airbyte": ab_resource},
        config={
            "ops": {
                "airbyte_sync_op": {
                    "config": {
                        "connection_id": DEFAULT_CONNECTION_ID,
                        "poll_interval": 0.1,
                        "poll_timeout": 10,
                    }
                }
            }
        },
    )
    def airbyte_sync_job():
        airbyte_sync_op(start_after=foo_op())

    with responses.RequestsMock() as rsps:

        rsps.add(rsps.POST, f"{ab_url}/connections/get", json={"name": "some_connection"})
        rsps.add(rsps.POST, f"{ab_url}/connections/sync", json={"job": {"id": 1}})
        rsps.add(rsps.POST, f"{ab_url}/jobs/get", json={"job": {"id": 1, "status": "running"}})
        rsps.add(rsps.POST, f"{ab_url}/jobs/get", json={"job": {"id": 1, "status": "succeeded"}})

        result = airbyte_sync_job.execute_in_process()
        assert result.output_for_node("airbyte_sync_op") == AirbyteOutput(
            job_details={"job": {"id": 1, "status": "succeeded"}},
            connection_details={"name": "some_connection"},
        )
