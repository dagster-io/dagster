from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_twilio.resources import (
    TwilioResource as TwilioResource,
    twilio_resource as twilio_resource,
)
from dagster_twilio.version import __version__

DagsterLibraryRegistry.register("dagster-twilio", __version__)

__all__ = ["twilio_resource"]
