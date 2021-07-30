from dagster import op, graph, schedule


@op(required_resource_keys={"abc"})
def foo(context):
    context.log(context.resources.abc)


@graph
def bar():
    foo()


@schedule(pipeline_name="bar", cron_schedule="1 1 * * *")
def bar_schedule(_):
    return {}
