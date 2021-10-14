from dagster import ModeDefinition, pipeline, resource, solid


@resource
def dummy_resource(context):
    context.log.info("IN RESOURCE")
    return "dummy_resource"


@solid
def dummy_solid(context):
    context.log.info("IN SOLID")


@pipeline(mode_defs=[ModeDefinition(resource_defs={"dr": dummy_resource})])
def pipe():
    dummy_solid()
