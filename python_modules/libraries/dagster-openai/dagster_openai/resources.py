from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Generator
from weakref import WeakKeyDictionary

from dagster import AssetExecutionContext, ConfigurableResource, InitResourceContext
from openai import Client
from pydantic import Field, PrivateAttr

context_to_counters = WeakKeyDictionary()


def add_to_asset_metadata(
    context: AssetExecutionContext, metadata_key: str, delta: int, output_name: str | None = None
):
    if context not in context_to_counters:
        context_to_counters[context] = defaultdict(lambda: 0)
    counters = context_to_counters[context]
    counters[metadata_key] += delta
    context.add_output_metadata(dict(counters), output_name)


def with_usage_metadata(context: AssetExecutionContext, output_name: str | None, func):
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
    """This resource is a thin wrapper over the
    `openai library <https://github.com/openai/openai-python>`_.
    """

    api_key: str = Field(description=("OpenAI API key. See https://platform.openai.com/api-keys"))

    _client: Client = PrivateAttr()

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Set up an OpenAI client based on the API key.
        self._client = Client(api_key=self.api_key)

    @contextmanager
    def get_client(
        self, context: AssetExecutionContext, output_name: str | None = None
    ) -> Generator[Client, None, None]:
        yield self._client

    @contextmanager
    def get_client_for_usage_metadata(
            self, context: AssetExecutionContext, output_name: str | None = None
    ) -> Generator[Client, None, None]:

        original_completions_create = self._client.completions.create
        original_embeddings_create = self._client.embeddings.create
        original_completions_create = self._client.chat.completions.create

        self._client.completions.create = with_usage_metadata(
            context, output_name, self._client.completions.create
        )
        self._client.embeddings.create = with_usage_metadata(
            context, output_name, self._client.embeddings.create
        )
        self._client.chat.completions.create = with_usage_metadata(
            context, output_name, self._client.chat.completions.create
        )

        try:
            yield self._client
        finally:
            self._client.completions.create = original_completions_create
            self._client.embeddings.create = original_embeddings_create
            self._client.chat.completions.create = original_completions_create

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        # Close OpenAI client.
        self._client.close()
