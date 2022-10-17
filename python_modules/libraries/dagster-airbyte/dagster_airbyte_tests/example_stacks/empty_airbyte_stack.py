import os

from dagster_airbyte import (
    AirbyteManagedStackReconciler,
    airbyte_resource,
)

airbyte_instance = airbyte_resource.configured(
    {
        "host": os.getenv("AIRBYTE_HOSTNAME", "localhost"),
        "port": os.getenv("AIRBYTE_PORT", "80"),
    }
)


reconciler = AirbyteManagedStackReconciler(
    airbyte=airbyte_instance,
    connections=[],
)
