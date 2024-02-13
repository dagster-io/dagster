from dagster._core.libraries import DagsterLibraryRegistry

from .resources import (
    TwilioResource as TwilioResource,
    twilio_resource as twilio_resource,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-twilio", __version__)

__all__ = ["twilio_resource"]
