from dagster_aws.s3.s3_fake_resource import create_s3_fake_resource
from dagster_aws.s3.solids import file_handle_to_s3

from dagster import ModeDefinition, ResourceDefinition, execute_pipeline, pipeline, solid
from dagster.utils.test import get_temp_file_handle_with_data


def create_file_handle_pipeline(temp_file_handle, s3_resource):
    @solid
    def emit_temp_handle(_):
        return temp_file_handle

    @pipeline(
        mode_defs=[
            ModeDefinition(resource_defs={'s3': ResourceDefinition.hardcoded_resource(s3_resource)})
        ]
    )
    def test():
        return file_handle_to_s3(emit_temp_handle())

    return test


def test_successful_file_handle_to_s3():
    foo_bytes = 'foo'.encode()
    with get_temp_file_handle_with_data(foo_bytes) as temp_file_handle:
        s3_fake_resource = create_s3_fake_resource()
        result = execute_pipeline(
            create_file_handle_pipeline(temp_file_handle, s3_fake_resource),
            environment_dict={
                'solids': {
                    'file_handle_to_s3': {'config': {'Bucket': 'some-bucket', 'Key': 'some-key'}}
                }
            },
        )

        assert result.success

        assert s3_fake_resource.session.mock_extras.upload_fileobj.call_count == 1

        assert (
            s3_fake_resource.session.get_object('some-bucket', 'some-key')['Body'].read()
            == foo_bytes
        )

        materializations = result.result_for_solid(
            'file_handle_to_s3'
        ).materializations_during_compute
        assert len(materializations) == 1
        assert len(materializations[0].metadata_entries) == 1
        assert (
            materializations[0].metadata_entries[0].entry_data.path == 's3://some-bucket/some-key'
        )
        assert materializations[0].metadata_entries[0].label == 'some-key'
