# ruff: noqa: SLF001
import importlib
import pickle
import sys
from unittest import mock

import pytest
from dagster import In, Int, Out, asset, job, op
from dagster._utils import PICKLE_PROTOCOL
from dagster._utils.env import environ
from dagster_cloud.serverless.io_manager import (
    PickledObjectServerlessIOManager,
    ServerlessPresignedURLIOManager,
    _build_serverless_io_manager,
    serverless_io_manager,
)
from upath import UPath

# ---------------------------------------------------------------------------
# Existing import test
# ---------------------------------------------------------------------------


@op(out=Out(Int))
def return_one():
    return 1


@op(
    ins={"num": In(Int)},
    out=Out(Int),
)
def add_one(num):
    return num + 1


@job(
    resource_defs={
        "io_manager": serverless_io_manager,
    }
)
def serverless_job():
    add_one(return_one())


def test_set_explicitly():
    # test that we can import and set the serverless_io_manager explicitly if desired
    assert serverless_job


# ---------------------------------------------------------------------------
# serverless_io_manager factory branch tests
# ---------------------------------------------------------------------------


def test_factory_returns_presigned_when_env_var_set():
    init_context = mock.MagicMock()
    init_context.instance.dagster_cloud_url = "https://myorg.agent.dagster.cloud"
    init_context.instance.dagster_cloud_agent_token = "test-token"
    init_context.instance.dagster_cloud_api_timeout = 30

    with environ({"SERVERLESS_IO_MANAGER_USE_PRESIGNED_URL": "True"}):
        manager = _build_serverless_io_manager(init_context)

    assert isinstance(manager, ServerlessPresignedURLIOManager)


def test_factory_returns_s3_when_env_var_not_set():
    init_context = mock.MagicMock()
    init_context.instance.deployment_name = "prod"

    with (
        environ(
            {
                "DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_BUCKET": "my-bucket",
                "DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_PREFIX": "org-storage/myorg",
            }
        ),
        mock.patch.object(
            PickledObjectServerlessIOManager,
            "_refresh_boto_session",
            return_value=(mock.MagicMock(), mock.MagicMock()),
        ),
    ):
        manager = _build_serverless_io_manager(init_context)

    assert isinstance(manager, PickledObjectServerlessIOManager)


# ---------------------------------------------------------------------------
# ServerlessPresignedURLIOManager unit tests
# ---------------------------------------------------------------------------

API_URL = "https://myorg.agent.dagster.cloud"
API_TOKEN = "test-token"
PRESIGNED_PUT_URL = "https://s3.amazonaws.com/bucket/key?X-Amz-Signature=put123"
PRESIGNED_GET_URL = "https://s3.amazonaws.com/bucket/key?X-Amz-Signature=get123"


def _make_manager() -> ServerlessPresignedURLIOManager:
    return ServerlessPresignedURLIOManager(api_url=API_URL, api_token=API_TOKEN, timeout=30)


def _presigned_url_response(url: str):
    resp = mock.MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"url": url}
    resp.raise_for_status.return_value = None
    return resp


def _s3_success_response(content: bytes = b""):
    resp = mock.MagicMock()
    resp.status_code = 200
    resp.content = content
    resp.raise_for_status.return_value = None
    return resp


def _s3_not_found_response():
    resp = mock.MagicMock()
    resp.status_code = 404
    return resp


def test_dump_to_path_calls_put():
    manager = _make_manager()
    obj = {"value": 42}
    path = UPath("storage/run-123/my_step/result")

    with (
        mock.patch.object(manager._session, "get") as mock_get_url,
        mock.patch.object(manager._session, "put") as mock_put,
    ):
        mock_get_url.return_value = _presigned_url_response(PRESIGNED_PUT_URL)
        mock_put.return_value = _s3_success_response()

        output_ctx = mock.MagicMock()
        manager.dump_to_path(output_ctx, obj, path)

        mock_get_url.assert_called_once()
        call_kwargs = mock_get_url.call_args
        assert "/gen_io_storage_url" in call_kwargs.args[0]
        assert call_kwargs.kwargs["params"] == {
            "key": "storage/run-123/my_step/result",
            "method": "PUT",
        }

        mock_put.assert_called_once()
        (put_url,) = mock_put.call_args.args
        assert put_url == PRESIGNED_PUT_URL
        put_data = mock_put.call_args.kwargs["data"]
        assert pickle.loads(put_data) == obj


def test_load_from_path_calls_get():
    manager = _make_manager()
    obj = {"value": 99}
    path = UPath("storage/run-123/my_step/result")
    pickled = pickle.dumps(obj, PICKLE_PROTOCOL)

    def fake_get(url, **kwargs):
        if "gen_io_storage_url" in url:
            return _presigned_url_response(PRESIGNED_GET_URL)
        return _s3_success_response(content=pickled)

    with mock.patch.object(manager._session, "get", side_effect=fake_get) as mock_get:
        input_ctx = mock.MagicMock()
        input_ctx.name = "result"
        result = manager.load_from_path(input_ctx, path)

        assert result == obj
        assert mock_get.call_count == 2
        assert mock_get.call_args_list[0].kwargs["params"] == {
            "key": "storage/run-123/my_step/result",
            "method": "GET",
        }
        assert mock_get.call_args_list[1].args[0] == PRESIGNED_GET_URL


def test_load_from_path_raises_file_not_found_on_404():
    manager = _make_manager()
    path = UPath("storage/run-123/my_step/result")

    def fake_get(url, **kwargs):
        if "gen_io_storage_url" in url:
            return _presigned_url_response(PRESIGNED_GET_URL)
        return _s3_not_found_response()

    with mock.patch.object(manager._session, "get", side_effect=fake_get):
        input_ctx = mock.MagicMock()
        input_ctx.name = "result"
        with pytest.raises(FileNotFoundError, match="result"):
            manager.load_from_path(input_ctx, path)


def test_dump_and_load_round_trip():
    manager = _make_manager()
    obj = [1, 2, 3, "hello"]
    path = UPath("my_asset")
    stored = {}

    def fake_put(url, *, data, timeout):
        stored["data"] = data
        return _s3_success_response()

    def fake_get(url, **kwargs):
        if "gen_io_storage_url" in url:
            return _presigned_url_response(PRESIGNED_PUT_URL if not stored else PRESIGNED_GET_URL)
        return _s3_success_response(content=stored["data"])

    with (
        mock.patch.object(manager._session, "get", side_effect=fake_get),
        mock.patch.object(manager._session, "put", side_effect=fake_put),
    ):
        output_ctx = mock.MagicMock()
        manager.dump_to_path(output_ctx, obj, path)

        input_ctx = mock.MagicMock()
        input_ctx.name = "result"
        result = manager.load_from_path(input_ctx, path)

    assert result == obj


def test_get_op_output_relative_path():
    manager = _make_manager()
    ctx = mock.MagicMock()
    ctx.get_identifier.return_value = ["run-abc", "my_step", "result"]
    path = manager.get_op_output_relative_path(ctx)
    assert path == UPath("storage/run-abc/my_step/result")


def test_path_exists_true_when_object_present():
    manager = _make_manager()
    path = UPath("storage/run-abc/my_step/result")

    head_resp = mock.MagicMock()
    head_resp.status_code = 200

    with (
        mock.patch.object(manager._session, "get") as mock_get_url,
        mock.patch.object(manager._session, "head") as mock_head,
    ):
        mock_get_url.return_value = _presigned_url_response(PRESIGNED_GET_URL)
        mock_head.return_value = head_resp

        assert manager.path_exists(path) is True
        assert mock_get_url.call_args.kwargs["params"]["method"] == "HEAD"
        mock_head.assert_called_once_with(PRESIGNED_GET_URL, timeout=30)


def test_path_exists_false_when_object_missing():
    manager = _make_manager()
    path = UPath("storage/run-abc/my_step/result")

    head_resp = mock.MagicMock()
    head_resp.status_code = 404

    with (
        mock.patch.object(manager._session, "get") as mock_get_url,
        mock.patch.object(manager._session, "head") as mock_head,
    ):
        mock_get_url.return_value = _presigned_url_response(PRESIGNED_GET_URL)
        mock_head.return_value = head_resp

        assert manager.path_exists(path) is False


def test_unlink_calls_delete():
    manager = _make_manager()
    path = UPath("storage/run-abc/my_step/result")
    presigned_delete_url = "https://s3.amazonaws.com/bucket/key?X-Amz-Signature=del123"

    with (
        mock.patch.object(manager._session, "get") as mock_get_url,
        mock.patch.object(manager._session, "delete") as mock_delete,
    ):
        mock_get_url.return_value = _presigned_url_response(presigned_delete_url)
        mock_delete.return_value = _s3_success_response()

        manager.unlink(path)

        assert mock_get_url.call_args.kwargs["params"]["method"] == "DELETE"
        mock_delete.assert_called_once_with(presigned_delete_url, timeout=30)


@asset
def my_asset():
    return 1


@asset
def downstream_asset(my_asset):
    return my_asset + 1


def test_serverless_io_manager_usable_in_job():
    from dagster import Definitions

    defs = Definitions(
        assets=[my_asset, downstream_asset],
        resources={"io_manager": serverless_io_manager},
    )
    assert defs


def test_module_imports_without_boto3_installed():
    # Simulates a v2 user pod whose image only depends on dagster-cloud (no
    # [serverless] extra) and therefore has no boto3 installed. The module must
    # still load cleanly so the presigned-URL IO manager path can be selected
    # at runtime via SERVERLESS_IO_MANAGER_USE_PRESIGNED_URL.
    cached = {
        name: sys.modules.pop(name)
        for name in (
            "boto3",
            "boto3.s3",
            "boto3.s3.transfer",
            "boto3.session",
            "botocore",
            "dagster_cloud.serverless",
            "dagster_cloud.serverless.io_manager",
        )
        if name in sys.modules
    }
    try:
        # `None` in sys.modules is the standard poison-pill that forces
        # `import boto3` to raise ImportError.
        with mock.patch.dict(sys.modules, {"boto3": None}):
            reloaded = importlib.import_module("dagster_cloud.serverless.io_manager")
            assert reloaded.ServerlessPresignedURLIOManager is not None
            # Instantiating the presigned-URL manager must not touch boto3.
            manager = reloaded.ServerlessPresignedURLIOManager(
                api_url=API_URL, api_token=API_TOKEN, timeout=30
            )
            assert manager is not None
    finally:
        # Drop anything we re-imported under the poison-pill and restore the
        # originals so other tests see a clean module state.
        for name in (
            "dagster_cloud.serverless",
            "dagster_cloud.serverless.io_manager",
        ):
            sys.modules.pop(name, None)
        sys.modules.update(cached)
        importlib.import_module("dagster_cloud.serverless.io_manager")
