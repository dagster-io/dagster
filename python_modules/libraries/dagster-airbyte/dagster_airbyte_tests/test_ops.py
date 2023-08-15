from base64 import b64encode

import pytest
import responses
from dagster import job, op
from dagster_airbyte import AirbyteOutput, airbyte_resource, airbyte_sync_op
from dagster_airbyte.resources import AirbyteCloudResource

DEFAULT_CONNECTION_ID = "02087b3c-2037-4db9-ae7b-4a8e45dc20b1"


@pytest.mark.parametrize(
    "forward_logs",
    [True, False],
)
@pytest.mark.parametrize(
    "additional_request_params",
    [False, True],
)
@pytest.mark.parametrize(
    "use_auth",
    [False, True],
)
def test_airbyte_sync_op(forward_logs, additional_request_params, use_auth):
    ab_host = "some_host"
    ab_port = "8000"
    ab_url = f"http://{ab_host}:{ab_port}/api/v1"
    ab_resource = airbyte_resource.configured(
        {
            "host": ab_host,
            "port": ab_port,
            "forward_logs": forward_logs,
            **(
                {"request_additional_params": {"headers": {"my-cool-header": "foo"}}}
                if additional_request_params
                else {}
            ),
            **({"username": "foo", "password": "bar"} if use_auth else {}),
        }
    )

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

        if forward_logs:
            rsps.add(rsps.POST, f"{ab_url}/jobs/get", json={"job": {"id": 1, "status": "running"}})
            rsps.add(
                rsps.POST, f"{ab_url}/jobs/get", json={"job": {"id": 1, "status": "succeeded"}}
            )
        else:
            rsps.add(
                rsps.POST,
                f"{ab_url}/jobs/list",
                json={"jobs": [{"job": {"id": 1, "status": "running"}}]},
            )
            rsps.add(
                rsps.POST,
                f"{ab_url}/jobs/list",
                json={"jobs": [{"job": {"id": 1, "status": "succeeded"}}]},
            )

        result = airbyte_sync_job.execute_in_process()
        assert result.output_for_node("airbyte_sync_op") == AirbyteOutput(
            job_details={"job": {"id": 1, "status": "succeeded"}},
            connection_details={"name": "some_connection"},
        )

        if additional_request_params:
            for call in rsps.calls:
                assert "my-cool-header" in call.request.headers

        if use_auth:
            for call in rsps.calls:
                encoded = b64encode(b"foo:bar").decode("utf-8")
                assert call.request.headers["Authorization"] == f"Basic {encoded}"
        else:
            for call in rsps.calls:
                assert "Authorization" not in call.request.headers


def test_airbyte_sync_op_cloud() -> None:
    ab_resource = AirbyteCloudResource(api_key="some_key")
    ab_url = ab_resource.api_base_url

    @op
    def foo_op() -> None:
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
    def airbyte_sync_job() -> None:
        airbyte_sync_op(start_after=foo_op())

    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            f"{ab_url}/jobs",
            json={"jobId": 1, "status": "pending", "jobType": "sync"},
        )

        rsps.add(
            rsps.GET,
            f"{ab_url}/jobs/1",
            json={"jobId": 1, "status": "running", "jobType": "sync"},
        )
        rsps.add(
            rsps.GET,
            f"{ab_url}/jobs/1",
            json={"jobId": 1, "status": "succeeded", "jobType": "sync"},
        )

        result = airbyte_sync_job.execute_in_process()
        assert result.output_for_node("airbyte_sync_op") == AirbyteOutput(
            job_details={"job": {"id": 1, "status": "succeeded"}},
            connection_details={},
        )

        for call in rsps.calls:
            assert call.request.headers["Authorization"] == "Bearer some_key"
