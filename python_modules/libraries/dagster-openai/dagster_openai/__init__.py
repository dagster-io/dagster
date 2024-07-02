from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import (
    OpenAIResource as OpenAIResource,
    with_usage_metadata as with_usage_metadata,
)

DagsterLibraryRegistry.register("dagster-openai", __version__)
