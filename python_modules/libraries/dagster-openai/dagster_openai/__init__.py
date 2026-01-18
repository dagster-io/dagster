from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_openai.resources import (
    OpenAIResource as OpenAIResource,
    with_usage_metadata as with_usage_metadata,
)
from dagster_openai.version import __version__

DagsterLibraryRegistry.register("dagster-openai", __version__)
