from dagster import resource


@resource
def no_step_launcher(_):
    return None
