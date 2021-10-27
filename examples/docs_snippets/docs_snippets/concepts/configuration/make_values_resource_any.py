from dagster import job, make_values_resource, op


@op(required_resource_keys={"value"})
def needs_value(context):
    context.log.info(f"value: {context.resources.value}")


@op(required_resource_keys={"value"})
def also_needs_value(context):
    context.log.info(f"value: {context.resources.value}")


@job(resource_defs={"value": make_values_resource()})
def basic_job():
    needs_value()
    also_needs_value()


basic_result = basic_job.execute_in_process(
    run_config={"resources": {"value": {"config": "some_value"}}}
)
