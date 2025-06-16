import dagster as dg


class SomeResource(dg.ConfigurableResource): ...


@dg.definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        resources={"some_resource": SomeResource(access_token="foo")},
    )
