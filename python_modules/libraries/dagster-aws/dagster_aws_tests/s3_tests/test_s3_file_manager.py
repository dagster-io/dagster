import uuid
from unittest import mock

import pytest
from botocore import exceptions
from dagster import DagsterResourceFunctionError, In, Out, build_op_context, configured, job, op
from dagster_aws.s3 import S3FileHandle, S3FileManager, s3_file_manager, s3_resource


def test_s3_file_manager_write(mock_s3_resource, mock_s3_bucket):
    file_manager = S3FileManager(mock_s3_resource.meta.client, mock_s3_bucket.name, "some-key")
    body = b"foo"

    file_handle = file_manager.write_data(body)
    assert mock_s3_bucket.Object(file_handle.s3_key).get()["Body"].read() == body

    file_handle = file_manager.write_data(body, ext="foo")
    assert file_handle.s3_key.endswith(".foo")
    assert mock_s3_bucket.Object(file_handle.s3_key).get()["Body"].read() == body


def test_s3_file_manager_read(mock_s3_resource, mock_s3_bucket):
    body = b"bar"
    remote_s3_object = mock_s3_bucket.Object("some-key/foo")
    remote_s3_object.put(Body=body)

    file_manager = S3FileManager(mock_s3_resource.meta.client, mock_s3_bucket.name, "some-key")
    file_handle = S3FileHandle(mock_s3_bucket.name, "some-key/foo")

    with file_manager.read(file_handle) as file_obj:
        assert file_obj.read() == body

    # read again. cached
    remote_s3_object.delete()
    with file_manager.read(file_handle) as file_obj:
        assert file_obj.read() == body


def test_depends_on_s3_resource_file_manager(mock_s3_bucket):
    bar_bytes = b"bar"

    @op(out=Out(S3FileHandle), required_resource_keys={"file_manager"})
    def emit_file(context):
        return context.resources.file_manager.write_data(bar_bytes)

    @op(
        ins={"file_handle": In(S3FileHandle)},
        required_resource_keys={"file_manager"},
    )
    def accept_file(context, file_handle):
        local_path = context.resources.file_manager.copy_handle_to_local_temp(file_handle)
        assert isinstance(local_path, str)
        assert open(local_path, "rb").read() == bar_bytes

    @job(resource_defs={"s3": s3_resource, "file_manager": s3_file_manager})
    def s3_file_manager_test():
        accept_file(emit_file())

    result = s3_file_manager_test.execute_in_process(
        run_config={
            "resources": {
                "file_manager": {
                    "config": {"s3_bucket": mock_s3_bucket.name, "s3_prefix": "some-prefix"}
                }
            },
        },
    )

    assert result.success

    keys_in_bucket = [obj.key for obj in mock_s3_bucket.objects.all()]

    assert len(keys_in_bucket) == 1

    file_key = list(keys_in_bucket)[0]
    comps = file_key.split("/")

    assert "/".join(comps[:-1]) == "some-prefix"

    assert uuid.UUID(comps[-1])


@mock.patch("boto3.session.Session.resource")
@mock.patch("dagster_aws.s3.resources.S3FileManager")
def test_s3_file_manager_resource(MockS3FileManager, mock_boto3_resource):
    did_it_run = dict(it_ran=False)

    resource_config = {
        "use_unsigned_session": True,
        "region_name": "us-west-1",
        "endpoint_url": "http://alternate-s3-host.io",
        "s3_bucket": "some-bucket",
        "s3_prefix": "some-prefix",
    }

    mock_s3_session = mock_boto3_resource.return_value.meta.client

    @op(required_resource_keys={"file_manager"})
    def test_op(context):
        # test that we got back a S3FileManager
        assert context.resources.file_manager == MockS3FileManager.return_value

        # make sure the file manager was initalized with the config we are supplying
        MockS3FileManager.assert_called_once_with(
            s3_session=mock_s3_session,
            s3_bucket=resource_config["s3_bucket"],
            s3_base_key=resource_config["s3_prefix"],
        )

        _, call_kwargs = mock_boto3_resource.call_args

        mock_boto3_resource.assert_called_once_with(
            "s3",
            region_name=resource_config["region_name"],
            endpoint_url=resource_config["endpoint_url"],
            use_ssl=True,
            config=call_kwargs["config"],
        )

        assert call_kwargs["config"].retries["max_attempts"] == 5

        did_it_run["it_ran"] = True

    context = build_op_context(
        resources={"file_manager": configured(s3_file_manager)(resource_config)}
    )
    test_op(context)

    assert did_it_run["it_ran"]


def test_s3_file_manager_resource_with_profile():

    resource_config = {
        "use_unsigned_session": True,
        "region_name": "us-west-1",
        "endpoint_url": "http://alternate-s3-host.io",
        "s3_bucket": "some-bucket",
        "s3_prefix": "some-prefix",
        "profile_name": "some-profile",
    }

    @op(required_resource_keys={"file_manager"})
    def test_op(context):
        # placeholder function to test resource initialization
        return context.log.info("return from test_solid")

    with pytest.raises(DagsterResourceFunctionError) as e:
        context = build_op_context(
            resources={"file_manager": configured(s3_file_manager)(resource_config)},
        )
        test_op(context)

    assert isinstance(e.value.user_exception, exceptions.ProfileNotFound)
    assert str(e.value.user_exception) == "The config profile (some-profile) could not be found"
