from dagster import op, graph, schedule


@op(required_resource_keys={"abc"}, config_schema={"efg": str})
def other_foo(context):
    context.log(context.resources.abc)


@graph
def other_bar():
    other_foo()


@schedule(pipeline_name="other_bar", cron_schedule="0 0 * * *")
def other_bar_schedule(_):
    return {}
