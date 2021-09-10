from dagster import DagsterEventType, graph, op
from dagster_aws.s3 import S3FileHandle, file_handle_to_s3, s3_file_manager, s3_resource


def create_file_handle_job(temp_file_handle):
    @op
    def emit_temp_handle(_):
        return temp_file_handle

    @graph
    def test():
        return file_handle_to_s3(emit_temp_handle())

    return test.to_job(resource_defs={"s3": s3_resource, "file_manager": s3_file_manager})


def test_successful_file_handle_to_s3(mock_s3_bucket):
    foo_bytes = b"foo"
    remote_s3_object = mock_s3_bucket.Object("some-key/foo")
    remote_s3_object.put(Body=foo_bytes)

    file_handle = S3FileHandle(mock_s3_bucket.name, "some-key/foo")
    result = create_file_handle_job(file_handle).execute_in_process(
        run_config={
            "solids": {
                "file_handle_to_s3": {"config": {"Bucket": mock_s3_bucket.name, "Key": "some-key"}}
            },
            "resources": {"file_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}},
        },
    )

    assert result.success

    assert mock_s3_bucket.Object(key="some-key").get()["Body"].read() == foo_bytes

    materializations = [
        event.step_materialization_data.materialization
        for event in result.result_for_node("file_handle_to_s3").event_list
        if event.event_type == DagsterEventType.ASSET_MATERIALIZATION
    ]
    assert len(materializations) == 1
    assert len(materializations[0].metadata_entries) == 1
    assert materializations[0].metadata_entries[
        0
    ].entry_data.path == "s3://{bucket}/some-key".format(bucket=mock_s3_bucket.name)
    assert materializations[0].metadata_entries[0].label == "some-key"
