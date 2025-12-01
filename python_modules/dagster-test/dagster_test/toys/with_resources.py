import dagster as dg


class SmallResource(dg.ConfigurableResource):
    small_field: str


class MediumResource(dg.ConfigurableResource):
    medium_field: str
    nested_resource: dg.ResourceDependency[SmallResource]


class LargeResource(dg.ConfigurableResource):
    large_field: str
    nested_resource: dg.ResourceDependency[MediumResource]


completed = {}


@dg.asset()
def the_asset(context, large_resource: LargeResource) -> None:
    context.log.info(large_resource)
    context.log.info(large_resource.nested_resource)
    context.log.info(large_resource.nested_resource.nested_resource)
    completed["yes"] = True


small_resource = SmallResource.configure_at_launch()
medium_resource = MediumResource.configure_at_launch(
    medium_field="new_medium_field", nested_resource=small_resource
)
large_resource = LargeResource.configure_at_launch(
    large_field="new_large_field", nested_resource=medium_resource
)


defs = dg.Definitions(
    assets=[the_asset],
    resources={
        "small_resource": small_resource,
        "medium_resource": medium_resource,
        "large_resource": large_resource,
    },
)
