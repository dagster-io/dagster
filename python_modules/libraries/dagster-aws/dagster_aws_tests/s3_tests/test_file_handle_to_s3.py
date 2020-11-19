from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster.utils.test import get_temp_file_handle_with_data
from dagster_aws.s3 import file_handle_to_s3, s3_resource


def create_file_handle_pipeline(temp_file_handle):
    @solid
    def emit_temp_handle(_):
        return temp_file_handle

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"s3": s3_resource})])
    def test():
        return file_handle_to_s3(emit_temp_handle())

    return test


def test_successful_file_handle_to_s3(bucket):
    foo_bytes = "foo".encode()
    with get_temp_file_handle_with_data(foo_bytes) as temp_file_handle:
        result = execute_pipeline(
            create_file_handle_pipeline(temp_file_handle),
            run_config={
                "solids": {
                    "file_handle_to_s3": {"config": {"Bucket": bucket.name, "Key": "some-key"}}
                }
            },
        )

        assert result.success

        assert bucket.Object(key="some-key").get()["Body"].read() == foo_bytes

        materializations = result.result_for_solid(
            "file_handle_to_s3"
        ).materializations_during_compute
        assert len(materializations) == 1
        assert len(materializations[0].metadata_entries) == 1
        assert materializations[0].metadata_entries[
            0
        ].entry_data.path == "s3://{bucket}/some-key".format(bucket=bucket.name)
        assert materializations[0].metadata_entries[0].label == "some-key"
