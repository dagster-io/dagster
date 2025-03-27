from dagster_shared.libraries import DagsterLibraryRegistry

from dagster_datahub.resources import (
    DatahubConnection,
    DatahubKafkaEmitterResource,
    DatahubRESTEmitterResource,
    datahub_kafka_emitter,
    datahub_rest_emitter,
)
from dagster_datahub.version import __version__

DagsterLibraryRegistry.register("dagster-datahub", __version__)

__all__ = [
    "DatahubConnection",
    "DatahubKafkaEmitterResource",
    "DatahubRESTEmitterResource",
    "datahub_kafka_emitter",
    "datahub_rest_emitter",
]
