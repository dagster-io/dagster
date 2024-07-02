from dagster._core.libraries import DagsterLibraryRegistry

from .version import __version__
from .resources import (
    DatahubConnection,
    DatahubRESTEmitterResource,
    DatahubKafkaEmitterResource,
    datahub_rest_emitter,
    datahub_kafka_emitter,
)

DagsterLibraryRegistry.register("dagster-datahub", __version__)

__all__ = [
    "datahub_rest_emitter",
    "datahub_kafka_emitter",
    "DatahubKafkaEmitterResource",
    "DatahubConnection",
    "DatahubRESTEmitterResource",
]
