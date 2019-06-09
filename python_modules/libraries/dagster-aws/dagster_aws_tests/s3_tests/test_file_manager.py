import os
from dagster.seven import mock

from dagster_aws.s3.file_manager import S3FileManager, S3FileHandle


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
    with file_manager.read(file_handle, 'rb') as file_obj:
        assert file_obj.read() == bar_bytes

    assert state['bucket'] == file_handle.s3_bucket
    assert state['key'] == file_handle.s3_key

    # read again. cached
    with file_manager.read(file_handle, 'rb') as file_obj:
        assert file_obj.read() == bar_bytes

    assert os.path.exists(state['file_name'])

    file_manager.cleanup_local_temp()

    assert not os.path.exists(state['file_name'])
