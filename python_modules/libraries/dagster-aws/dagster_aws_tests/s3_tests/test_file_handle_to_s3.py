from dagster import pipeline, solid, ModeDefinition, execute_pipeline, ResourceDefinition
from dagster.utils.test import get_temp_file_handle_with_data
from dagster_aws.s3.solids import file_handle_to_s3
from dagster_aws.s3.s3_fake_resource import create_s3_fake_resource


def create_file_handle_pipeline(temp_file_handle, s3_resource):
    # pylint: disable=no-value-for-parameter

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

        assert s3_fake_resource.session.mock_extras.put_object.call_count == 1

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


def test_successful_file_handle_to_s3_with_configs():
    foo_bytes = 'foo'.encode()
    with get_temp_file_handle_with_data(foo_bytes) as temp_file_handle:
        s3_fake_resource = create_s3_fake_resource()

        result = execute_pipeline(
            create_file_handle_pipeline(temp_file_handle, s3_fake_resource),
            environment_dict={
                'solids': {
                    'file_handle_to_s3': {
                        'config': {
                            'Bucket': 'some-bucket',
                            'Key': 'some-key',
                            'CacheControl': 'some-value',
                        }
                    }
                }
            },
        )

        assert result.success

        s3_fake_resource.session.mock_extras.put_object.assert_called_once_with(
            CacheControl='some-value'
        )
