import pytest
import responses
from dagster import Failure, build_init_resource_context
from dagster_airbyte import airbyte_resource, AirbyteOutput, AirbyteState


@responses.activate
def test_trigger_connection():
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    resp = ab_resource.start_sync("some_connection")
    assert resp == {"job": {"id": 1}}


def test_trigger_connection_fail():
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={"host": "some_host", "port": "8000", "request_max_retries": 1}
        )
    )
    responses.add(
        method=responses.POST, url=ab_resource.api_base_url + "/connections/sync", status=500
    )
    with pytest.raises(Failure, match="Exceeded max number of retries"):
        ab_resource.sync_and_poll("some_connection")


@responses.activate
@pytest.mark.parametrize(
    "state",
    [AirbyteState.SUCCEEDED, AirbyteState.CANCELLED, AirbyteState.ERROR, "unrecognized"],
)
def test_sync_and_pool(state):
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs/get",
        json={"job": {"id": 1, "status": state}},
        status=200,
    )

    if state == AirbyteState.ERROR:
        with pytest.raises(Failure, match="Job failed"):
            r = ab_resource.sync_and_poll("some_connection", 0)

    elif state == AirbyteState.CANCELLED:
        with pytest.raises(Failure, match="Job was cancelled"):
            r = ab_resource.sync_and_poll("some_connection", 0)

    elif state == "unrecognized":
        with pytest.raises(Failure, match="unexpected state"):
            r = ab_resource.sync_and_poll("some_connection", 0)

    else:
        r = ab_resource.sync_and_poll("some_connection", 0)
        assert r == AirbyteOutput({"id": 1, "status": state})


@responses.activate
def test_sync_and_poll_timeout():
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/sync",
        json={"job": {"id": 1}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs/get",
        json={"job": {"id": 1, "status": "pending"}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs/get",
        json={"job": {"id": 1, "status": "running"}},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs/get",
        json={"job": {"id": 1, "status": "running"}},
        status=200,
    )
    poll_wait_second = 2
    timeout = 1
    with pytest.raises(Failure, match="Timeout: Airbyte job"):
        ab_resource.sync_and_poll("some_connection", poll_wait_second, timeout)
