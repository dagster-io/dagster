from collections import defaultdict
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Generator, Optional, Union
from weakref import WeakKeyDictionary

from dagster import AssetExecutionContext, OpExecutionContext, ConfigurableResource, InitResourceContext
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


def add_to_asset_metadata(
    context: AssetExecutionContext, usage_metadata: dict, output_name: Optional[str] = None
):
    if context not in context_to_counters:
        context_to_counters[context] = defaultdict(lambda: 0)
    counters = context_to_counters[context]

    for metadata_key, delta in usage_metadata.items():
        counters[metadata_key] += delta
    context.add_output_metadata(dict(counters), output_name)


def with_usage_metadata(context: AssetExecutionContext, output_name: Optional[str], func):
    """This wrapper can be used on any endpoint of the
    `openai library <https://github.com/openai/openai-python>`
    to log the OpenAI API usage metadata in the asset metadata.

    Examples:
    .. code-block:: python

        import os

        from dagster import AssetExecutionContext, Definitions, EnvVar, asset, define_asset_job
        from dagster_openai import OpenAIResource, with_usage_metadata

        # TODO add comment to example different behaviour
        @asset(compute_kind="OpenAI")
        def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
            with openai.get_client(context) as client:
                client.fine_tuning.jobs.create = with_usage_metadata(
                    context=context,
                    output_name="some_output_name",
                    func=client.fine_tuning.jobs.create
                )
                client.fine_tuning.jobs.create(
                    model="gpt-3.5-turbo",
                    training_file="some_training_file"
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
    if not isinstance(context, AssetExecutionContext):
        raise TypeError("The `with_usage_metadata` can only be used when context is of type AssetExecutionContext.")

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
        add_to_asset_metadata(context, usage_metadata, output_name)

        return response

    return wrapper


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
        for attribute_names in API_ENDPOINT_CLASSES_TO_ENDPOINT_METHODS_MAPPING[
            api_endpoint_class
        ]:
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
        self._client = Client(api_key=self.api_key)

    @contextmanager
    def get_client(
        self,
        context: Union[AssetExecutionContext, OpExecutionContext],
        output_name: Optional[str] = None,
    ) -> Generator[Client, None, None]:
        """Returns an ``openai.Client`` for interacting with the OpenAI API.

        By default, in an asset context, the client comes with wrapped endpoints
        for three API resources, Completions, Embeddings and Chat,
        allowing to log the API usage metadata in the asset metadata.

        Note that the endpoints are not and can not be wrapped
        to automatically capture the API usage metadata in an op context.

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
        if isinstance(context, AssetExecutionContext):
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
