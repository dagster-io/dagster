from dagster import resource


@resource
def prod_external_service():
    ...


@resource
def dev_external_service():
    ...
