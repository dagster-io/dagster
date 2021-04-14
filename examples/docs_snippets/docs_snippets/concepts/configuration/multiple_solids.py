from dagster import ModeDefinition, execute_pipeline, pipeline, resource, solid


@resource(config_schema=str)
def my_str_resource(init_context):
    return init_context.resource_config


@solid(required_resource_keys={"my_str"})
def solid1(context):
    context.log.info("solid1: " + context.resources.my_str)


@solid(required_resource_keys={"my_str"})
def solid2(context):
    context.log.info("solid2: " + context.resources.my_str)


@pipeline(mode_defs=[ModeDefinition(resource_defs={"my_str": my_str_resource})])
def my_pipeline():
    solid1()
    solid2()


execute_pipeline(my_pipeline, run_config={"resources": {"my_str": "some_value"}})
