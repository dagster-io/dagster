from unittest.mock import ANY, MagicMock, patch

import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    AssetSpec,
    Definitions,
    OpExecutionContext,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    graph_asset,
    materialize_to_memory,
    multi_asset,
    op,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.init import build_init_resource_context
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_openai import OpenAIResource, with_usage_metadata

TEST_MODEL = "test_model"


@patch("dagster_openai.resources.Client")
def test_openai_client(mock_client) -> None:
    openai_resource = OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
    openai_resource.setup_for_execution(build_init_resource_context())

    mock_context = MagicMock()
    with openai_resource.get_client(mock_context):
        mock_client.assert_called_once_with(
            api_key="xoxp-1234123412341234-12341234-1234",
            organization=None,
            project=None,
            base_url=None,
        )


@patch("dagster_openai.resources.Client")
def test_openai_client_with_config(mock_client) -> None:
    openai_resource = OpenAIResource(
        api_key="xoxp-1234123412341234-12341234-1234",
        organization="foo",
        project="bar",
        base_url="http://foo.bar",
    )
    openai_resource.setup_for_execution(build_init_resource_context())

    mock_context = MagicMock()
    with openai_resource.get_client(mock_context):
        mock_client.assert_called_once_with(
            api_key="xoxp-1234123412341234-12341234-1234",
            organization="foo",
            project="bar",
            base_url="http://foo.bar",
        )


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.OpExecutionContext", autospec=OpExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_op(mock_client, mock_context, mock_wrapper):
    @op
    def openai_op(openai_resource: OpenAIResource):
        assert openai_resource

        with openai_resource.get_client(context=mock_context) as client:
            client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
            )

        assert mock_client.called
        assert not mock_wrapper.called

    result = wrap_op_in_graph_and_execute(
        openai_op,
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )
    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_asset(mock_client, mock_context, mock_wrapper):
    @asset
    def openai_asset(openai_resource: OpenAIResource):
        assert openai_resource

        with openai_resource.get_client(context=mock_context) as client:
            client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
            )

        assert mock_client.called
        assert mock_wrapper.call_count == 3

    result = materialize_to_memory(
        [openai_asset],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_graph_backed_asset(mock_client, mock_context, mock_wrapper):
    @op
    def model_version_op():
        return "gpt-3.5-turbo"

    @op
    def message_op():
        return {"role": "user", "content": "Say this is a test"}

    @op
    def openai_op(openai_resource: OpenAIResource, model_version, message):
        assert openai_resource

        with openai_resource.get_client(context=mock_context) as client:
            client.chat.completions.create(model=model_version, messages=[message])

        assert mock_client.called
        assert mock_wrapper.called

    @graph_asset
    def openai_asset():
        return openai_op(model_version_op(), message_op())

    result = materialize_to_memory(
        [openai_asset],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_multi_asset(mock_client, mock_context, mock_wrapper):
    @multi_asset(
        specs=[AssetSpec("status"), AssetSpec("result")],
    )
    def openai_multi_asset(openai_resource: OpenAIResource):
        assert openai_resource

        mock_context.assets_def.keys_by_output_name.keys.return_value = [
            AssetKey("status"),
            AssetKey("result"),
        ]
        mock_context.output_for_asset_key.return_value = "result"

        # Test success when asset_key is provided
        with openai_resource.get_client_for_asset(
            context=mock_context, asset_key=AssetKey("result")
        ) as client:
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

        # Test failure when asset_key is not provided
        with pytest.raises(DagsterInvariantViolationError):
            with openai_resource.get_client(context=mock_context) as client:
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say this is a test"}],
                )
        return None, None

    result = materialize_to_memory(
        [openai_multi_asset],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_resource_with_partitioned_asset(mock_client, mock_context, mock_wrapper):
    openai_partitions_def = StaticPartitionsDefinition([str(j) for j in range(5)])

    openai_partitioned_assets = []

    for i in range(5):

        @asset(
            name=f"openai_partitioned_asset_{i}",
            group_name="openai_partitioned_assets",
            partitions_def=openai_partitions_def,
        )
        def openai_partitioned_asset(openai_resource: OpenAIResource):
            assert openai_resource

            mock_context.output_for_asset_key.return_value = "test"

            with openai_resource.get_client(context=mock_context) as client:
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say this is a test"}],
                )

            assert mock_client.called
            assert mock_wrapper.called
            mock_wrapper.assert_called_with(
                api_endpoint_class=ANY,
                context=mock_context,
                output_name="test",
            )

        openai_partitioned_assets.append(openai_partitioned_asset)

    defs = Definitions(
        assets=openai_partitioned_assets,
        jobs=[
            define_asset_job(
                name="openai_partitioned_asset_job",
                selection=AssetSelection.groups("openai_partitioned_assets"),
                partitions_def=openai_partitions_def,
            )
        ],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    for partition_key in openai_partitions_def.get_partition_keys():
        result = defs.get_job_def("openai_partitioned_asset_job").execute_in_process(
            partition_key=partition_key
        )
        assert result.success

    expected_wrapper_call_counts = (
        3 * len(openai_partitioned_assets) * len(openai_partitions_def.get_partition_keys())
    )
    assert mock_wrapper.call_count == expected_wrapper_call_counts


@patch("dagster.OpExecutionContext", autospec=OpExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_wrapper_with_op(mock_client, mock_context):
    @op
    def openai_op(openai_resource: OpenAIResource):
        assert openai_resource

        with openai_resource.get_client(context=mock_context) as client:
            with pytest.raises(DagsterInvariantViolationError):
                client.fine_tuning.jobs.create = with_usage_metadata(
                    context=mock_context,
                    output_name="some_output_name",
                    func=client.fine_tuning.jobs.create,
                )

    result = wrap_op_in_graph_and_execute(
        openai_op,
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )
    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_wrapper_with_asset(mock_client, mock_context, mock_wrapper):
    @asset
    def openai_asset(openai_resource: OpenAIResource):
        assert openai_resource

        mock_completion = MagicMock()
        mock_completion.model = TEST_MODEL
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 1
        mock_usage.total_tokens = 1
        mock_usage.completion_tokens = 1
        mock_completion.usage = mock_usage
        mock_client.return_value.fine_tuning.jobs.create.return_value = mock_completion

        with openai_resource.get_client(context=mock_context) as client:
            client.fine_tuning.jobs.create = with_usage_metadata(
                context=mock_context,
                output_name="openai_asset",
                func=client.fine_tuning.jobs.create,
            )
            client.fine_tuning.jobs.create(
                model="gpt-3.5-turbo", training_file="some_training_file"
            )

            mock_context.add_output_metadata.assert_called_with(
                metadata={
                    "openai.model": TEST_MODEL,
                    "openai.calls": 1,
                    "openai.total_tokens": 1,
                    "openai.prompt_tokens": 1,
                    "openai.completion_tokens": 1,
                },
                output_name="openai_asset",
            )

    result = materialize_to_memory(
        [openai_asset],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_wrapper_with_graph_backed_asset(mock_client, mock_context, mock_wrapper):
    @op
    def model_version_op():
        return "gpt-3.5-turbo"

    @op
    def training_file_op():
        return "some_training_file"

    @op
    def openai_op(openai_resource: OpenAIResource, model_version, training_file):
        assert openai_resource

        mock_completion = MagicMock()
        mock_completion.model = TEST_MODEL
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 1
        mock_usage.total_tokens = 1
        mock_usage.completion_tokens = 1
        mock_completion.usage = mock_usage
        mock_client.return_value.fine_tuning.jobs.create.return_value = mock_completion

        with openai_resource.get_client(context=mock_context) as client:
            client.fine_tuning.jobs.create = with_usage_metadata(
                context=mock_context,
                output_name="openai_asset",
                func=client.fine_tuning.jobs.create,
            )
            client.fine_tuning.jobs.create(model=model_version, training_file=training_file)

            mock_context.add_output_metadata.assert_called_with(
                metadata={
                    "openai.model": TEST_MODEL,
                    "openai.calls": 1,
                    "openai.total_tokens": 1,
                    "openai.prompt_tokens": 1,
                    "openai.completion_tokens": 1,
                },
                output_name="openai_asset",
            )

    @graph_asset
    def openai_asset():
        return openai_op(model_version_op(), training_file_op())

    result = materialize_to_memory(
        [openai_asset],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster.AssetExecutionContext", autospec=AssetExecutionContext)
@patch("dagster_openai.resources.Client")
def test_openai_wrapper_with_multi_asset(mock_client, mock_context, mock_wrapper):
    @multi_asset(
        specs=[AssetSpec("status"), AssetSpec("result")],
    )
    def openai_multi_asset(openai_resource: OpenAIResource):
        assert openai_resource

        mock_completion = MagicMock()
        mock_completion.model = TEST_MODEL
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 1
        mock_usage.total_tokens = 1
        mock_usage.completion_tokens = 1
        mock_completion.usage = mock_usage
        mock_client.return_value.fine_tuning.jobs.create.return_value = mock_completion

        with openai_resource.get_client_for_asset(
            context=mock_context, asset_key=AssetKey("result")
        ) as client:
            client.fine_tuning.jobs.create = with_usage_metadata(
                context=mock_context,
                output_name="result",
                func=client.fine_tuning.jobs.create,
            )
            client.fine_tuning.jobs.create(
                model="gpt-3.5-turbo", training_file="some_training_file"
            )

            mock_context.add_output_metadata.assert_called_with(
                metadata={
                    "openai.model": TEST_MODEL,
                    "openai.calls": 1,
                    "openai.total_tokens": 1,
                    "openai.prompt_tokens": 1,
                    "openai.completion_tokens": 1,
                },
                output_name="result",
            )
        return None, None

    result = materialize_to_memory(
        [openai_multi_asset],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    assert result.success


@patch("dagster_openai.resources.OpenAIResource._wrap_with_usage_metadata")
@patch("dagster_openai.resources.Client")
def test_openai_wrapper_with_partitioned_asset(mock_client, mock_wrapper):
    openai_partitions_def = StaticPartitionsDefinition([str(j) for j in range(5)])

    openai_partitioned_assets = []

    for i in range(5):

        @asset(
            name=f"openai_partitioned_asset_{i}",
            group_name="openai_partitioned_assets",
            partitions_def=openai_partitions_def,
        )
        def openai_partitioned_asset(openai_resource: OpenAIResource):
            assert openai_resource

            mock_context = MagicMock()
            mock_context.__class__ = AssetExecutionContext

            mock_completion = MagicMock()
            mock_completion.model = TEST_MODEL
            mock_usage = MagicMock()
            mock_usage.prompt_tokens = 1
            mock_usage.total_tokens = 1
            mock_usage.completion_tokens = 1
            mock_completion.usage = mock_usage
            mock_client.return_value.fine_tuning.jobs.create.return_value = mock_completion

            with openai_resource.get_client(context=mock_context) as client:
                client.fine_tuning.jobs.create = with_usage_metadata(
                    context=mock_context,
                    output_name=None,
                    func=client.fine_tuning.jobs.create,
                )
                client.fine_tuning.jobs.create(
                    model="gpt-3.5-turbo", training_file="some_training_file"
                )
                mock_context.add_output_metadata.assert_called_with(
                    {
                        "openai.model": TEST_MODEL,
                        "openai.calls": 1,
                        "openai.total_tokens": 1,
                        "openai.prompt_tokens": 1,
                        "openai.completion_tokens": 1,
                    },
                    None,
                )

        openai_partitioned_assets.append(openai_partitioned_asset)

    defs = Definitions(
        assets=openai_partitioned_assets,
        jobs=[
            define_asset_job(
                name="openai_partitioned_asset_job",
                selection=AssetSelection.groups("openai_partitioned_assets"),
                partitions_def=openai_partitions_def,
            )
        ],
        resources={
            "openai_resource": OpenAIResource(api_key="xoxp-1234123412341234-12341234-1234")
        },
    )

    for partition_key in openai_partitions_def.get_partition_keys():
        result = defs.get_job_def("openai_partitioned_asset_job").execute_in_process(
            partition_key=partition_key
        )
        assert result.success
