import dagster as dg


class SomeResource(dg.ConfigurableResource): ...


@dg.definitions
def defs() -> dg.Definitions:
    return dg.Definitions(
        # highlight-start
        resources={
            "some_resource": SomeResource(access_token=dg.EnvVar("MY_ACCESS_TOKEN"))
        },
        # highlight-end
    )
