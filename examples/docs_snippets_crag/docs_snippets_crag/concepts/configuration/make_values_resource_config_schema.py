from dagster import job, make_values_resource, op


@op(required_resource_keys={"values"})
def needs_value(context):
    context.log.info(f"my str: {context.resources.values['my_str']}")


@op(required_resource_keys={"values"})
def needs_different_value(context):
    context.log.info(f"my int: {context.resources.values['my_int']}")


@job(resource_defs={"values": make_values_resource(my_str=str, my_int=int)})
def different_values_job():
    needs_value()
    needs_different_value()


result = different_values_job.execute_in_process(
    run_config={"resources": {"values": {"config": {"my_str": "foo", "my_int": 1}}}}
)
