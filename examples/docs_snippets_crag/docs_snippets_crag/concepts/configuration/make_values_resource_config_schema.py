from dagster import make_values_resource, graph, op


@op(required_resource_keys={"values"})
def needs_value(context):
    context.log.info(f"my str: {context.resources.values['my_str']}")


@op(required_resource_keys={"values"})
def needs_different_value(context):
    context.log.info(f"my int: {context.resources.values['my_int']}")


@graph
def different_values_required():
    needs_value()
    needs_different_value()


different_values_job = different_values_required.to_job(
    resource_defs={"values": make_values_resource(my_str=str, my_int=int)}
)

result = different_values_job.execute_in_process(
    run_config={"resources": {"values": {"config": {"my_str": "foo", "my_int": 1}}}}
)
