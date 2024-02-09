from collections import defaultdict
from contextlib import contextmanager
from enum import Enum
from functools import wraps
from typing import Generator, List, Optional
from weakref import WeakKeyDictionary

from dagster import AssetExecutionContext, ConfigurableResource, InitResourceContext
from openai import Client
from pydantic import Field, PrivateAttr


class ApiResourceEnum(Enum):
    """Legacy and current resources of the OpenAI API v1."""

    COMPLETIONS = "completions"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    FILES = "files"
    IMAGES = "images"
    AUDIO = "audio"
    MODERATIONS = "moderations"
    MODELS = "models"
    FINE_TUNING = "fine_tuning"


API_RESOURCES_TO_ENDPOINT_METHODS_MAPPING = {
    "completions": [["create"]],
    "chat": [["completions", "create"]],
    "embeddings": [["create"]],
    "files": [
        ["create"],
        ["retrieve"],
        ["list"],
        ["delete"],
        ["content"],
        ["retrieve_content"],
        ["wait_for_processing"],
    ],
    "images": [["create_variation"], ["edit"], ["generate"]],
    "audio": [["transcriptions", "create"], ["translations", "create"], ["speech", "create"]],
    "moderations": [["create"]],
    "models": [["retrieve"], ["list"], ["delete"]],
    "fine_tuning": [
        ["jobs", "create"],
        ["jobs", "retrieve"],
        ["jobs", "list"],
        ["jobs", "cancel"],
        ["jobs", "list_events"],
    ],
}

context_to_counters = WeakKeyDictionary()


def add_to_asset_metadata(
    context: AssetExecutionContext, metadata_key: str, delta: int, output_name: Optional[str] = None
):
    if context not in context_to_counters:
        context_to_counters[context] = defaultdict(lambda: 0)
    counters = context_to_counters[context]
    counters[metadata_key] += delta
    context.add_output_metadata(dict(counters), output_name)


def with_usage_metadata(context: AssetExecutionContext, output_name: Optional[str], func):
    """This wrapped can be used on any endpoint of the
    `openai library <https://github.com/openai/openai-python>`
    to log the OpenAI API usage to asset metadata.

    Examples:
    .. code-block:: python

        import os

        from dagster import asset, define_asset_job, EnvVar
        from dagster_openai import OpenAIResource, with_usage_metadata


        @asset(compute_kind="OpenAI")
        def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
            with openai.get_client(context) as client:
                client.fine_tuning.jobs.create = with_usage_metadata(
                    client.fine_tuning.jobs.create
                )
                client.fine_tuning.jobs.create(
                    model="gpt-3.5-turbo",
                    training_file="some_training_file"
                )

        openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")

        defs = Definitions(
            jobs=[openai_asset_job],
            resources={
                "slack": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
            },
        )
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        usage = response.usage
        add_to_asset_metadata(context, "openai.calls", 1, output_name)
        add_to_asset_metadata(context, "openai.total_tokens", usage.total_tokens, output_name)
        add_to_asset_metadata(context, "openai.prompt_tokens", usage.prompt_tokens, output_name)
        if hasattr(usage, "completion_tokens"):
            add_to_asset_metadata(
                context, "openai.completion_tokens", usage.completion_tokens, output_name
            )
        return response

    return wrapper


class OpenAIResource(ConfigurableResource):
    """This resource is wrapper over the
    `openai library <https://github.com/openai/openai-python>`_.

    By configuring this OpenAI resource, you can interact with OpenAI API
    and log its usage to asset metadata.

    Examples:
        .. code-block:: python

            import os

            from dagster import asset, define_asset_job, EnvVar
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
                jobs=[openai_asset_job],
                resources={
                    "slack": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
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
        client_resource: ApiResourceEnum,
        context: AssetExecutionContext,
        output_name: Optional[str],
    ):
        for attribute_names in API_RESOURCES_TO_ENDPOINT_METHODS_MAPPING[client_resource.value]:
            curr = self._client.__getattribute__(client_resource.value)
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
        context: AssetExecutionContext,
        output_name: Optional[str] = None,
        api_resources: Optional[List[ApiResourceEnum]] = None,
    ) -> Generator[Client, None, None]:
        """Returns an ``openai.Client`` for interacting with the OpenAI API.

        By default, the client comes with wrapped endpoints
        for three API resources, Completions, Embeddings and Chat,
        allowing to log the API usage in the asset metadata.

        Note that, if required by your use case, you can specify the API resources
        for which you would like the endpoints to be wrapped.
        Legacy and current resources of OpenAI API v1 can be specified using `ApiResourceEnum`.

        Examples:
        .. code-block:: python

            import os

            from dagster import asset, define_asset_job, EnvVar
            from dagster_openai import OpenAIResource, ApiResourceEnum


            @asset(compute_kind="OpenAI")
            def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
                api_resources = [
                    ApiResourceEnum.CHAT,
                    ApiResourceEnum.FINE_TUNING,
                ]
                with openai.get_client(context, api_resources=api_resources) as client:
                    client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Say this is a test"}]
                    )

            openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")

            defs = Definitions(
                jobs=[openai_asset_job],
                resources={
                    "slack": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
                },
            )
        """
        # If none of the OpenAI API resource types are specified,
        # we wrap by default the methods of
        # `openai.resources.Completions`, `openai.resources.Embeddings`
        # and `openai.resources.chat.Completions`.
        # This allows the usage metadata to be captured.
        if not api_resources:
            api_resources = [
                ApiResourceEnum.COMPLETIONS,
                ApiResourceEnum.CHAT,
                ApiResourceEnum.EMBEDDINGS,
            ]
        for client_resource in api_resources:
            self._wrap_with_usage_metadata(
                client_resource=client_resource,
                context=context,
                output_name=output_name,
            )
        yield self._client

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # Close OpenAI client.
        self._client.close()
