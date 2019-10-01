import os
import uuid

from dagster_aws.s3.file_manager import S3FileHandle, S3FileManager
from dagster_aws.s3.s3_fake_resource import create_s3_fake_resource
from dagster_aws.s3.system_storage import s3_plus_default_storage_defs

from dagster import (
    InputDefinition,
    Int,
    ModeDefinition,
    OutputDefinition,
    ResourceDefinition,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.seven import mock

# For deps


def test_s3_file_manager_write():
    s3_mock = mock.MagicMock()
    file_manager = S3FileManager(s3_mock, 'some-bucket', 'some-key')

    foo_bytes = 'foo'.encode()

    file_handle = file_manager.write_data(foo_bytes)

    assert isinstance(file_handle, S3FileHandle)

    assert file_handle.s3_bucket == 'some-bucket'
    assert file_handle.s3_key.startswith('some-key/')

    assert s3_mock.put_object.call_count == 1


def test_s3_file_manager_read():
    state = {'called': 0}
    bar_bytes = 'bar'.encode()

    class S3Mock(mock.MagicMock):
        def download_file(self, *_args, **kwargs):
            state['called'] += 1
            assert state['called'] == 1
            state['bucket'] = kwargs.get('Bucket')
            state['key'] = kwargs.get('Key')
            file_name = kwargs.get('Filename')
            state['file_name'] = file_name
            with open(file_name, 'wb') as ff:
                ff.write(bar_bytes)

    s3_mock = S3Mock()
    file_manager = S3FileManager(s3_mock, 'some-bucket', 'some-key')
    file_handle = S3FileHandle('some-bucket', 'some-key/kdjfkjdkfjkd')
    with file_manager.read(file_handle) as file_obj:
        assert file_obj.read() == bar_bytes

    assert state['bucket'] == file_handle.s3_bucket
    assert state['key'] == file_handle.s3_key

    # read again. cached
    with file_manager.read(file_handle) as file_obj:
        assert file_obj.read() == bar_bytes

    assert os.path.exists(state['file_name'])

    file_manager.delete_local_temp()

    assert not os.path.exists(state['file_name'])


def test_depends_on_s3_resource_intermediates():
    @solid(
        input_defs=[InputDefinition('num_one', Int), InputDefinition('num_two', Int)],
        output_defs=[OutputDefinition(Int)],
    )
    def add_numbers(_, num_one, num_two):
        return num_one + num_two

    s3_fake_resource = create_s3_fake_resource()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                system_storage_defs=s3_plus_default_storage_defs,
                resource_defs={'s3': ResourceDefinition.hardcoded_resource(s3_fake_resource)},
            )
        ]
    )
    def s3_internal_pipeline():
        return add_numbers()

    result = execute_pipeline(
        s3_internal_pipeline,
        environment_dict={
            'solids': {
                'add_numbers': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 4}}}
            },
            'storage': {'s3': {'config': {'s3_bucket': 'some-bucket'}}},
        },
    )

    assert result.success
    assert result.result_for_solid('add_numbers').output_value() == 6

    assert 'some-bucket' in s3_fake_resource.session.buckets

    keys = set()
    for step_key, output_name in [('add_numbers.compute', 'result')]:
        keys.add(create_s3_key(result.run_id, step_key, output_name))

    assert set(s3_fake_resource.session.buckets['some-bucket'].keys()) == keys


def create_s3_key(run_id, step_key, output_name):
    return 'dagster/storage/{run_id}/intermediates/{step_key}/{output_name}'.format(
        run_id=run_id, step_key=step_key, output_name=output_name
    )


def test_depends_on_s3_resource_file_manager():
    bar_bytes = 'bar'.encode()

    @solid(output_defs=[OutputDefinition(S3FileHandle)])
    def emit_file(context):
        return context.file_manager.write_data(bar_bytes)

    @solid(input_defs=[InputDefinition('file_handle', S3FileHandle)])
    def accept_file(context, file_handle):
        local_path = context.file_manager.copy_handle_to_local_temp(file_handle)
        assert isinstance(local_path, str)
        assert open(local_path, 'rb').read() == bar_bytes

    s3_fake_resource = create_s3_fake_resource()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                system_storage_defs=s3_plus_default_storage_defs,
                resource_defs={'s3': ResourceDefinition.hardcoded_resource(s3_fake_resource)},
            )
        ]
    )
    def s3_file_manager_test():
        accept_file(emit_file())

    result = execute_pipeline(
        s3_file_manager_test,
        environment_dict={'storage': {'s3': {'config': {'s3_bucket': 'some-bucket'}}}},
    )

    assert result.success

    keys_in_bucket = set(s3_fake_resource.session.buckets['some-bucket'].keys())

    for step_key, output_name in [
        ('emit_file.compute', 'result'),
        ('accept_file.compute', 'result'),
    ]:
        keys_in_bucket.remove(create_s3_key(result.run_id, step_key, output_name))

    assert len(keys_in_bucket) == 1

    file_key = list(keys_in_bucket)[0]
    comps = file_key.split('/')

    assert '/'.join(comps[:-1]) == 'dagster/storage/{run_id}/files'.format(run_id=result.run_id)

    assert uuid.UUID(comps[-1])
