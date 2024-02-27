from dagster._core.libraries import DagsterLibraryRegistry

from .resources import (
    OpenAIResource as OpenAIResource,
    with_usage_metadata as with_usage_metadata,
)

# TODO: replace version by `__version__` when we add back a version.py file and publish library to pypi.
#  Import with `from .version import __version__`
DagsterLibraryRegistry.register("dagster-openai", "1!0+dev")
