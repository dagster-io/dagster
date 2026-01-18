import dagster as dg


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={})
