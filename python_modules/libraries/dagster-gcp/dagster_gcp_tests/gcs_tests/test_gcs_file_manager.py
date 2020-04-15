from dagster_gcp.gcs.file_manager import GCSFileHandle, GCSFileManager
from google.cloud import storage

from dagster.seven import mock


def test_gcs_file_manager_write():
    gcs_mock = mock.MagicMock()
    file_manager = GCSFileManager(storage.client.Client(), 'some-bucket', 'some-key')
    file_manager._client = gcs_mock  # pylint:disable=protected-access

    foo_bytes = 'foo'.encode()

    file_handle = file_manager.write_data(foo_bytes)

    assert isinstance(file_handle, GCSFileHandle)

    assert file_handle.gcs_bucket == 'some-bucket'
    assert file_handle.gcs_key.startswith('some-key/')

    assert gcs_mock.get_bucket().blob().upload_from_file.call_count == 1

    file_handle = file_manager.write_data(foo_bytes, ext='foo')

    assert isinstance(file_handle, GCSFileHandle)

    assert file_handle.gcs_bucket == 'some-bucket'
    assert file_handle.gcs_key.startswith('some-key/')
    assert file_handle.gcs_key[-4:] == '.foo'

    assert gcs_mock.get_bucket().blob().upload_from_file.call_count == 2
