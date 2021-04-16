from dagster import ModeDefinition, execute_pipeline, make_values_resource, pipeline, solid


@solid(required_resource_keys={"value"})
def solid1(context):
    context.log.info(f"value: {context.resources.value}")


@solid(required_resource_keys={"value"})
def solid2(context):
    context.log.info(f"value: {context.resources.value}")


@pipeline(mode_defs=[ModeDefinition(resource_defs={"value": make_values_resource()})])
def my_pipeline():
    solid1()
    solid2()


execute_pipeline(my_pipeline, run_config={"resources": {"value": {"config": "some_value"}}})
