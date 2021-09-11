from dagster import make_values_resource, op, graph


@op(required_resource_keys={"value"})
def needs_value(context):
    context.log.info(f"value: {context.resources.value}")


@op(required_resource_keys={"value"})
def also_needs_value(context):
    context.log.info(f"value: {context.resources.value}")


@graph
def basic():
    needs_value()
    also_needs_value()


basic_job = basic.to_job(resource_defs={"value": make_values_resource()})

basic_result = basic_job.execute_in_process(
    run_config={"resources": {"value": {"config": "some_value"}}}
)
