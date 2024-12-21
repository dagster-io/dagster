from dagster import Definitions, ResourceParam, asset


class SomeResource: ...


@asset
def an_asset(some_resource: ResourceParam[SomeResource]) -> None: ...


defs = Definitions([an_asset], resources={"some_resource": SomeResource()})
