import os

from dagster_airbyte import AirbyteManagedElementReconciler, airbyte_resource

airbyte_instance = airbyte_resource.configured(
    {
        "host": os.getenv("AIRBYTE_HOSTNAME", "localhost"),
        "port": os.getenv("AIRBYTE_PORT", "80"),
    }
)


reconciler = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[],
    delete_unmentioned_resources=True,
)


reconciler_no_delete = AirbyteManagedElementReconciler(
    airbyte=airbyte_instance,
    connections=[],
    delete_unmentioned_resources=False,
)
