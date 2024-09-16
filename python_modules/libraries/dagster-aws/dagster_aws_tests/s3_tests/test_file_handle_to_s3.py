from typing import Any

import pytest
from dagster import DagsterEventType, job, op
from dagster._core.definitions.metadata import MetadataValue

from dagster_aws.s3 import (
    S3FileHandle,
    S3FileManagerResource,
    S3Resource,
    file_handle_to_s3,
    s3_file_manager,
    s3_resource,
)


@pytest.fixture(name="s3_resource_type", params=[True, False])
def s3_resource_type_fixture(request) -> Any:
    if request.param:
        return s3_resource
    else:
        return S3Resource.configure_at_launch()


@pytest.fixture(name="s3_file_manager_resource_type", params=[True, False])
def s3_file_manager_resource_type_fixture(request) -> Any:
    if request.param:
        return s3_file_manager
    else:
        return S3FileManagerResource.configure_at_launch()


def create_file_handle_job(temp_file_handle, s3_resource_type, s3_file_manager_resource_type):
    @op
    def emit_temp_handle(_):
        return temp_file_handle

    @job(resource_defs={"s3": s3_resource_type, "file_manager": s3_file_manager_resource_type})
    def test():
        file_handle_to_s3(emit_temp_handle())

    return test


def test_successful_file_handle_to_s3(
    mock_s3_bucket, s3_resource_type, s3_file_manager_resource_type
):
    foo_bytes = b"foo"
    remote_s3_object = mock_s3_bucket.Object("some-key/foo")
    remote_s3_object.put(Body=foo_bytes)

    file_handle = S3FileHandle(mock_s3_bucket.name, "some-key/foo")
    result = create_file_handle_job(
        file_handle, s3_resource_type, s3_file_manager_resource_type
    ).execute_in_process(
        run_config={
            "ops": {
                "file_handle_to_s3": {"config": {"Bucket": mock_s3_bucket.name, "Key": "some-key"}}
            },
            "resources": {"file_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}},
        },
    )

    assert result.success

    assert mock_s3_bucket.Object(key="some-key").get()["Body"].read() == foo_bytes

    materializations = [
        event.step_materialization_data.materialization
        for event in result.events_for_node("file_handle_to_s3")
        if event.event_type == DagsterEventType.ASSET_MATERIALIZATION
    ]
    assert len(materializations) == 1
    assert len(materializations[0].metadata) == 1
    assert materializations[0].metadata["some-key"] == MetadataValue.path(
        f"s3://{mock_s3_bucket.name}/some-key"
    )
