from dagster import resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource


@dagster_maintained_resource
@resource
def no_step_launcher(_):
    return None
