from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import (
    TwilioResource as TwilioResource,
    twilio_resource as twilio_resource,
)

DagsterLibraryRegistry.register("dagster-twilio", __version__)

__all__ = ["twilio_resource"]
