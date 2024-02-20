import json

import pytest
from dagster import (
    AssetExecutionContext,
    AssetOut,
    AssetSelection,
    Definitions,
    OpExecutionContext,
    asset,
    define_asset_job,
    multi_asset,
    op,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.init import build_init_resource_context
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_openai import OpenAIResource
from mock import ANY, MagicMock, patch


@patch("dagster_openai.resources.Client")
def test_openai_client(mock_client) -> None:
    openai_resource = OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
    openai_resource.setup_for_execution(build_init_resource_context())

    mock_context = MagicMock()
    with openai_resource.get_client(mock_context):
        mock_client.assert_called_once_with(api_key="xoxp-1234123412341234-12341234-1234")


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_op(mock_client, mock_wrapper):
    @op
    def openai_op(openai_resource: OpenAIResource):
        assert openai_resource
        body = {"ok": True}
        mock_client.chat.completions.create.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        mock_context = MagicMock()
        mock_context.__class__ = OpExecutionContext
        with openai_resource.get_client(context=mock_context) as client:
            client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
            )

        assert mock_client.called
        assert mock_wrapper.not_called

    result = wrap_op_in_graph_and_execute(
        openai_op,
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )
    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_asset(mock_client, mock_wrapper):
    @asset
    def openai_asset(openai_resource: OpenAIResource):
        assert openai_resource
        body = {"ok": True}
        mock_client.chat.completions.create.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        mock_context = MagicMock()
        mock_context.__class__ = AssetExecutionContext
        with openai_resource.get_client(context=mock_context) as client:
            client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
            )

        assert mock_client.called
        assert mock_wrapper.call_count == 3

    result = (
        Definitions(
            assets=[openai_asset],
            jobs=[
                define_asset_job(
                    name="openai_asset_job", selection=AssetSelection.assets(openai_asset)
                )
            ],
            resources={
                "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
            },
        )
        .get_job_def("openai_asset_job")
        .execute_in_process()
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_multi_asset_with_asset_key(mock_client, mock_wrapper):
    @multi_asset(
        outs={
            "status": AssetOut(),
            "result": AssetOut(),
        },
    )
    def openai_multi_asset(openai_resource: OpenAIResource):
        assert openai_resource
        body = {"ok": True}
        mock_client.chat.completions.create.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        mock_context = MagicMock()
        mock_context.__class__ = AssetExecutionContext
        with openai_resource.get_client(context=mock_context, asset_key="result") as client:
            client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
            )

        assert mock_client.called
        assert mock_wrapper.call_count == 3
        mock_wrapper.assert_called_with(
            api_endpoint_class=ANY,
            context=mock_context,
            output_name="result",
        )
        return None, None

    result = (
        Definitions(
            assets=[openai_multi_asset],
            jobs=[define_asset_job("openai_asset_job")],
            resources={
                "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
            },
        )
        .get_job_def("openai_asset_job")
        .execute_in_process()
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_multi_asset_without_asset_key(mock_client, mock_wrapper):
    @multi_asset(
        outs={
            "status": AssetOut(),
            "result": AssetOut(),
        },
    )
    def openai_multi_asset(openai_resource: OpenAIResource):
        assert openai_resource
        body = {"ok": True}
        mock_client.chat.completions.create.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        mock_context = MagicMock()
        mock_context.__class__ = AssetExecutionContext
        mock_context.assets_def.keys_by_output_name.keys.return_value = ["status", "result"]
        with pytest.raises(DagsterInvariantViolationError):
            with openai_resource.get_client(context=mock_context) as client:
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say this is a test"}],
                )
        return None, None

    result = (
        Definitions(
            assets=[openai_multi_asset],
            jobs=[define_asset_job("openai_asset_job")],
            resources={
                "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
            },
        )
        .get_job_def("openai_asset_job")
        .execute_in_process()
    )

    assert result.success
