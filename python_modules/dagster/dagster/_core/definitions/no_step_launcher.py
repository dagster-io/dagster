from dagster import resource
from dagster._annotations import dagster_maintained


@dagster_maintained
@resource
def no_step_launcher(_):
    return None
