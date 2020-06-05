import sys
import zipfile

import boto3
from dagster_aws.s3 import S3FileHandle, s3_system_storage
from dagster_examples.airline_demo.unzip_file_handle import unzip_file_handle
from moto import mock_s3

from dagster import (
    LocalFileHandle,
    ModeDefinition,
    OutputDefinition,
    ResourceDefinition,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.utils.test import get_temp_file_name

# for dep graphs


def write_zip_file_to_disk(zip_file_path, archive_member, data):
    with zipfile.ZipFile(zip_file_path, mode='w') as archive:
        # writable stream with archive.open not available < 3.6
        if sys.version_info.major < 3:
            # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            archive.writestr(bytes=data, zinfo_or_arcname=archive_member)
        else:
            archive.writestr(data=data, zinfo_or_arcname=archive_member)


def test_unzip_file_handle():
    data = 'foo'.encode()

    with get_temp_file_name() as zip_file_name:
        write_zip_file_to_disk(zip_file_name, 'some_archive_member', data)

        @solid
        def to_zip_file_handle(_):
            return LocalFileHandle(zip_file_name)

        @pipeline
        def do_test_unzip_file_handle():
            return unzip_file_handle(to_zip_file_handle())

        result = execute_pipeline(
            do_test_unzip_file_handle,
            environment_dict={
                'solids': {
                    'unzip_file_handle': {
                        'inputs': {'archive_member': {'value': 'some_archive_member'}}
                    }
                }
            },
        )
        assert result.success


@mock_s3
def test_unzip_file_handle_on_fake_s3():
    foo_bytes = 'foo'.encode()

    @solid(output_defs=[OutputDefinition(S3FileHandle)])
    def write_zipped_file_to_s3_store(context):
        with get_temp_file_name() as zip_file_name:
            write_zip_file_to_disk(zip_file_name, 'an_archive_member', foo_bytes)
            with open(zip_file_name, 'rb') as ff:
                s3_file_handle = context.file_manager.write_data(ff.read())
                return s3_file_handle

    # Uses mock S3
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket='some-bucket')

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={'s3': ResourceDefinition.hardcoded_resource(s3)},
                system_storage_defs=[s3_system_storage],
            )
        ]
    )
    def do_test_unzip_file_handle_s3():
        return unzip_file_handle(write_zipped_file_to_s3_store())

    result = execute_pipeline(
        do_test_unzip_file_handle_s3,
        environment_dict={
            'storage': {'s3': {'config': {'s3_bucket': 'some-bucket'}}},
            'solids': {
                'unzip_file_handle': {'inputs': {'archive_member': {'value': 'an_archive_member'}}}
            },
        },
    )

    assert result.success

    zipped_s3_file = result.result_for_solid('write_zipped_file_to_s3_store').output_value()
    unzipped_s3_file = result.result_for_solid('unzip_file_handle').output_value()
    bucket_keys = [obj['Key'] for obj in s3.list_objects(Bucket='some-bucket')['Contents']]

    assert zipped_s3_file.s3_key in bucket_keys
    assert unzipped_s3_file.s3_key in bucket_keys
