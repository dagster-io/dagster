import re

import pytest
import responses
from dagster import (
    DagsterExecutionInterruptedError,
    Failure,
    MetadataEntry,
    _check as check,
    build_init_resource_context,
)
from dagster_airbyte import AirbyteOutput, AirbyteState, airbyte_resource, AirbyteCloudResource
from dagster_airbyte.utils import generate_materializations

from .utils import get_sample_connection_json, get_sample_job_json, get_sample_job_list_json


@responses.activate
def test_trigger_connection() -> None:
    ab_resource = AirbyteCloudResource(api_key="some_key")
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json={"jobId": 1, "status": "pending", "jobType": "sync"},
        status=200,
    )
    resp = ab_resource.start_sync("some_connection")
    assert resp == {"job": {"id": 1, "status": "pending"}}


def test_trigger_connection_fail() -> None:
    ab_resource = AirbyteCloudResource(api_key="some_key")
    with pytest.raises(
        Failure,
        match=re.escape("Max retries (3) exceeded with url: https://api.airbyte.com/v1/jobs."),
    ):
        ab_resource.sync_and_poll("some_connection")


@responses.activate
@pytest.mark.parametrize(
    "state",
    [AirbyteState.SUCCEEDED, AirbyteState.CANCELLED, AirbyteState.ERROR, "unrecognized"],
)
def test_sync_and_poll(state) -> None:
    ab_resource = AirbyteCloudResource(api_key="some_key")
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json={"jobId": 1, "status": "pending", "jobType": "sync"},
        status=200,
    )
    responses.add(
        method=responses.GET,
        url=ab_resource.api_base_url + "/jobs/1",
        json={"jobId": 1, "status": state, "jobType": "sync"},
        status=200,
    )

    if state == "unrecognized":
        responses.add(
            responses.DELETE,
            f"{ab_resource.api_base_url}/jobs/1",
            status=200,
            json={"jobId": 1, "status": "cancelled", "jobType": "sync"},
        )

    if state == AirbyteState.ERROR:
        with pytest.raises(Failure, match="Job failed"):
            ab_resource.sync_and_poll("some_connection", 0)

    elif state == AirbyteState.CANCELLED:
        with pytest.raises(Failure, match="Job was cancelled"):
            ab_resource.sync_and_poll("some_connection", 0)

    elif state == "unrecognized":
        with pytest.raises(Failure, match="unexpected state"):
            ab_resource.sync_and_poll("some_connection", 0)

    else:
        result = ab_resource.sync_and_poll("some_connection", 0)
        assert result == AirbyteOutput(
            job_details={"job": {"id": 1, "status": state}},
            connection_details={},
        )


@responses.activate
def test_start_sync_bad_out_fail() -> None:
    ab_resource = AirbyteCloudResource(api_key="some_key")

    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/jobs",
        json=None,
        status=500,
    )
    with pytest.raises(
        Failure,
        match=re.escape("Max retries (3) exceeded with url: https://api.airbyte.com/v1/jobs."),
    ):
        ab_resource.start_sync("some_connection")
