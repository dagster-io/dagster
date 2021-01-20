from dagster import ModeDefinition, configured, execute_pipeline, pipeline, solid
from dagster.seven import mock
from dagster_gcp.gcs.file_manager import GCSFileHandle, GCSFileManager
from dagster_gcp.gcs.resources import gcs_file_manager
from google.cloud import storage


def test_gcs_file_manager_write():
    gcs_mock = mock.MagicMock()
    file_manager = GCSFileManager(storage.client.Client(), "some-bucket", "some-key")
    file_manager._client = gcs_mock  # pylint:disable=protected-access

    foo_bytes = b"foo"

    file_handle = file_manager.write_data(foo_bytes)

    assert isinstance(file_handle, GCSFileHandle)

    assert file_handle.gcs_bucket == "some-bucket"
    assert file_handle.gcs_key.startswith("some-key/")

    assert gcs_mock.get_bucket().blob().upload_from_file.call_count == 1

    file_handle = file_manager.write_data(foo_bytes, ext="foo")

    assert isinstance(file_handle, GCSFileHandle)

    assert file_handle.gcs_bucket == "some-bucket"
    assert file_handle.gcs_key.startswith("some-key/")
    assert file_handle.gcs_key[-4:] == ".foo"

    assert gcs_mock.get_bucket().blob().upload_from_file.call_count == 2


@mock.patch("dagster_gcp.gcs.resources.storage.client.Client")
@mock.patch("dagster_gcp.gcs.resources.GCSFileManager")
def test_gcs_file_manger_resource(MockGCSFileManager, mock_storage_client_Client):
    did_it_run = dict(it_ran=False)

    resource_config = {
        "project": "some-project",
        "gcs_bucket": "some-bucket",
        "gcs_prefix": "some-prefix",
    }

    @solid(required_resource_keys={"file_manager"})
    def test_solid(context):
        # test that we got back a GCSFileManager
        assert context.resources.file_manager == MockGCSFileManager.return_value

        # make sure the file manager was initalized with the config we are supplying
        MockGCSFileManager.assert_called_once_with(
            client=mock_storage_client_Client.return_value,
            gcs_bucket=resource_config["gcs_bucket"],
            gcs_base_key=resource_config["gcs_prefix"],
        )
        mock_storage_client_Client.assert_called_once_with(project=resource_config["project"])

        did_it_run["it_ran"] = True

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"file_manager": configured(gcs_file_manager)(resource_config)},
            )
        ]
    )
    def test_pipeline():
        test_solid()

    execute_pipeline(test_pipeline)
    assert did_it_run["it_ran"]
