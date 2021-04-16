from dagster import ModeDefinition, execute_pipeline, make_values_resource, pipeline, solid


@solid(required_resource_keys={"values"})
def solid1(context):
    context.log.info(f"my str: {context.resources.values['my_str']}")


@solid(required_resource_keys={"values"})
def solid2(context):
    context.log.info(f"my int: {context.resources.values['my_int']}")


@pipeline(
    mode_defs=[
        ModeDefinition(resource_defs={"values": make_values_resource(my_str=str, my_int=int)})
    ]
)
def my_pipeline():
    solid1()
    solid2()


execute_pipeline(
    my_pipeline, run_config={"resources": {"values": {"config": {"my_str": "foo", "my_int": 1}}}}
)
