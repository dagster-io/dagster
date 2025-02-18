from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Optional, Union
from weakref import WeakKeyDictionary

from dagster import (
    AssetExecutionContext,
    AssetKey,
    ConfigurableResource,
    InitResourceContext,
    OpExecutionContext,
)
from dagster._annotations import public
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from openai import Client
from pydantic import Field, PrivateAttr


class ApiEndpointClassesEnum(Enum):
    """Supported endpoint classes of the OpenAI API v1."""

    COMPLETIONS = "completions"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"


API_ENDPOINT_CLASSES_TO_ENDPOINT_METHODS_MAPPING = {
    ApiEndpointClassesEnum.COMPLETIONS: [["create"]],
    ApiEndpointClassesEnum.CHAT: [["completions", "create"]],
    ApiEndpointClassesEnum.EMBEDDINGS: [["create"]],
}

context_to_counters = WeakKeyDictionary()


def _add_to_asset_metadata(
    context: AssetExecutionContext, usage_metadata: dict, output_name: Optional[str]
):
    if context not in context_to_counters:
        context_to_counters[context] = defaultdict(lambda: 0)
    counters = context_to_counters[context]

    for metadata_key, delta in usage_metadata.items():
        counters[metadata_key] += delta
    context.add_output_metadata(dict(counters), output_name)


@public
def with_usage_metadata(
    context: Union[AssetExecutionContext, OpExecutionContext], output_name: Optional[str], func
):
    """This wrapper can be used on any endpoint of the
    `openai library <https://github.com/openai/openai-python>`
    to log the OpenAI API usage metadata in the asset metadata.

    Examples:
        .. code-block:: python

            from dagster import (
                AssetExecutionContext,
                AssetKey,
                AssetSelection,
                AssetSpec,
                Definitions,
                EnvVar,
                MaterializeResult,
                asset,
                define_asset_job,
                multi_asset,
            )
            from dagster_openai import OpenAIResource, with_usage_metadata


            @asset(compute_kind="OpenAI")
            def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
                with openai.get_client(context) as client:
                    client.fine_tuning.jobs.create = with_usage_metadata(
                        context=context, output_name="some_output_name", func=client.fine_tuning.jobs.create
                    )
                    client.fine_tuning.jobs.create(model="gpt-3.5-turbo", training_file="some_training_file")


            openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")


            @multi_asset(
                specs=[
                    AssetSpec("my_asset1"),
                    AssetSpec("my_asset2"),
                ]
            )
            def openai_multi_asset(context: AssetExecutionContext, openai: OpenAIResource):
                with openai.get_client(context, asset_key=AssetKey("my_asset1")) as client:
                    client.chat.completions.create(
                        model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
                    )

                # The materialization of `my_asset1` will include both OpenAI usage metadata
                # and the metadata added when calling `MaterializeResult`.
                return (
                    MaterializeResult(asset_key="my_asset1", metadata={"foo": "bar"}),
                    MaterializeResult(asset_key="my_asset2", metadata={"baz": "qux"}),
                )


            openai_multi_asset_job = define_asset_job(
                name="openai_multi_asset_job", selection=AssetSelection.assets(openai_multi_asset)
            )


            defs = Definitions(
                assets=[openai_asset, openai_multi_asset],
                jobs=[openai_asset_job, openai_multi_asset_job],
                resources={
                    "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
                },
            )
    """
    if not isinstance(context, AssetExecutionContext):
        raise DagsterInvariantViolationError(
            "The `with_usage_metadata` can only be used when context is of type `AssetExecutionContext`."
        )

    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage = response.usage
        usage_metadata = {
            "openai.calls": 1,
            "openai.total_tokens": usage.total_tokens,
            "openai.prompt_tokens": usage.prompt_tokens,
        }
        if hasattr(usage, "completion_tokens"):
            usage_metadata["openai.completion_tokens"] = usage.completion_tokens
        _add_to_asset_metadata(context, usage_metadata, output_name)

        return response

    return wrapper


@public
class OpenAIResource(ConfigurableResource):
    """This resource is wrapper over the
    `openai library <https://github.com/openai/openai-python>`_.

    By configuring this OpenAI resource, you can interact with OpenAI API
    and log its usage metadata in the asset metadata.

    Examples:
        .. code-block:: python

            import os

            from dagster import AssetExecutionContext, Definitions, EnvVar, asset, define_asset_job
            from dagster_openai import OpenAIResource


            @asset(compute_kind="OpenAI")
            def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
                with openai.get_client(context) as client:
                    client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Say this is a test"}]
                    )

            openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")

            defs = Definitions(
                assets=[openai_asset],
                jobs=[openai_asset_job],
                resources={
                    "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
                },
            )
    """

    api_key: str = Field(description=("OpenAI API key. See https://platform.openai.com/api-keys"))
    organization: Optional[str] = Field(default=None)
    project: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)

    _client: Client = PrivateAttr()

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _wrap_with_usage_metadata(
        self,
        api_endpoint_class: ApiEndpointClassesEnum,
        context: AssetExecutionContext,
        output_name: Optional[str],
    ):
        for attribute_names in API_ENDPOINT_CLASSES_TO_ENDPOINT_METHODS_MAPPING[api_endpoint_class]:
            curr = self._client.__getattribute__(api_endpoint_class.value)
            # Get the second to last attribute from the attribute list to reach the method.
            i = 0
            while i < len(attribute_names) - 1:
                curr = curr.__getattribute__(attribute_names[i])
                i += 1
            # Wrap the method.
            curr.__setattr__(
                attribute_names[i],
                with_usage_metadata(
                    context=context,
                    output_name=output_name,
                    func=curr.__getattribute__(attribute_names[i]),
                ),
            )

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Set up an OpenAI client based on the API key.
        self._client = Client(
            api_key=self.api_key,
            organization=self.organization,
            project=self.project,
            base_url=self.base_url,
        )

    @public
    @contextmanager
    def get_client(
        self, context: Union[AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext]
    ) -> Generator[Client, None, None]:
        """Yields an ``openai.Client`` for interacting with the OpenAI API.

        By default, in an asset context, the client comes with wrapped endpoints
        for three API resources, Completions, Embeddings and Chat,
        allowing to log the API usage metadata in the asset metadata.

        Note that the endpoints are not and cannot be wrapped
        to automatically capture the API usage metadata in an op context.

        :param context: The ``context`` object for computing the op or asset in which ``get_client`` is called.

        Examples:
            .. code-block:: python

                from dagster import (
                    AssetExecutionContext,
                    Definitions,
                    EnvVar,
                    GraphDefinition,
                    OpExecutionContext,
                    asset,
                    define_asset_job,
                    op,
                )
                from dagster_openai import OpenAIResource


                @op
                def openai_op(context: OpExecutionContext, openai: OpenAIResource):
                    with openai.get_client(context) as client:
                        client.chat.completions.create(
                            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
                        )


                openai_op_job = GraphDefinition(name="openai_op_job", node_defs=[openai_op]).to_job()


                @asset(compute_kind="OpenAI")
                def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
                    with openai.get_client(context) as client:
                        client.chat.completions.create(
                            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
                        )


                openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")

                defs = Definitions(
                    assets=[openai_asset],
                    jobs=[openai_asset_job, openai_op_job],
                    resources={
                        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
                    },
                )
        """
        yield from self._get_client(context=context, asset_key=None)

    @public
    @contextmanager
    def get_client_for_asset(
        self, context: AssetExecutionContext, asset_key: AssetKey
    ) -> Generator[Client, None, None]:
        """Yields an ``openai.Client`` for interacting with the OpenAI.

        When using this method, the OpenAI API usage metadata is automatically
        logged in the asset materializations associated with the provided ``asset_key``.

        By default, the client comes with wrapped endpoints
        for three API resources, Completions, Embeddings and Chat,
        allowing to log the API usage metadata in the asset metadata.

        This method can only be called when working with assets,
        i.e. the provided ``context`` must be of type ``AssetExecutionContext``.

        :param context: The ``context`` object for computing the asset in which ``get_client`` is called.
        :param asset_key: the ``asset_key`` of the asset for which a materialization should include the metadata.

        Examples:
            .. code-block:: python

                from dagster import (
                    AssetExecutionContext,
                    AssetKey,
                    AssetSpec,
                    Definitions,
                    EnvVar,
                    MaterializeResult,
                    asset,
                    define_asset_job,
                    multi_asset,
                )
                from dagster_openai import OpenAIResource


                @asset(compute_kind="OpenAI")
                def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
                    with openai.get_client_for_asset(context, context.asset_key) as client:
                        client.chat.completions.create(
                            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
                        )


                openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")


                @multi_asset(specs=[AssetSpec("my_asset1"), AssetSpec("my_asset2")], compute_kind="OpenAI")
                def openai_multi_asset(context: AssetExecutionContext, openai_resource: OpenAIResource):
                    with openai_resource.get_client_for_asset(context, asset_key=AssetKey("my_asset1")) as client:
                        client.chat.completions.create(
                            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Say this is a test"}]
                        )
                    return (
                        MaterializeResult(asset_key="my_asset1", metadata={"some_key": "some_value1"}),
                        MaterializeResult(asset_key="my_asset2", metadata={"some_key": "some_value2"}),
                    )


                openai_multi_asset_job = define_asset_job(
                    name="openai_multi_asset_job", selection="openai_multi_asset"
                )

                defs = Definitions(
                    assets=[openai_asset, openai_multi_asset],
                    jobs=[openai_asset_job, openai_multi_asset_job],
                    resources={
                        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
                    },
                )
        """
        yield from self._get_client(context=context, asset_key=asset_key)

    def _get_client(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext, OpExecutionContext],
        asset_key: Optional[AssetKey] = None,
    ) -> Generator[Client, None, None]:
        if isinstance(context, AssetExecutionContext):
            if asset_key is None:
                if len(context.assets_def.keys_by_output_name.keys()) > 1:
                    raise DagsterInvariantViolationError(
                        "The argument `asset_key` must be specified for multi_asset with more than one asset."
                    )
                asset_key = context.asset_key
            output_name = context.output_for_asset_key(asset_key)
            # By default, when the resource is used in an asset context,
            # we wrap the methods of `openai.resources.Completions`,
            # `openai.resources.Embeddings` and `openai.resources.chat.Completions`.
            # This allows the usage metadata to be captured in the asset metadata.
            api_endpoint_classes = [
                ApiEndpointClassesEnum.COMPLETIONS,
                ApiEndpointClassesEnum.CHAT,
                ApiEndpointClassesEnum.EMBEDDINGS,
            ]
            for api_endpoint_class in api_endpoint_classes:
                self._wrap_with_usage_metadata(
                    api_endpoint_class=api_endpoint_class,
                    context=context,
                    output_name=output_name,
                )
        yield self._client

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # Close OpenAI client.
        self._client.close()
