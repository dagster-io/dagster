from dagster import ResourceDefinition, graph, op


@op(config_schema={"config_param": str}, required_resource_keys={"my_resource"})
def do_something(context):
    context.log.info("config_param: " + context.op_config["config_param"])
    context.log.info("my_resource: " + context.resources.my_resource)


@graph
def do_it_all():
    do_something()


do_it_all_job = do_it_all.to_job(
    config={"ops": {"do_something": {"config": {"config_param": "stuff"}}}},
    resource_defs={"my_resource": ResourceDefinition.hardcoded_resource("hello")},
)
