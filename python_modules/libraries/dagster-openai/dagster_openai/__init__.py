from dagster._core.libraries import DagsterLibraryRegistry

from .resources import (
    OpenAIResource as OpenAIResource,
    with_usage_metadata as with_usage_metadata,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-openai", __version__)
