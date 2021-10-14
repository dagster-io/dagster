from dagster import graph, op


@op(config_schema={"config_param": str})
def do_something(context):
    context.log.info("config_param: " + context.op_config["config_param"])


@graph
def do_it_all():
    do_something()


do_it_all_with_default_config = do_it_all.to_job(
    config={"ops": {"do_something": {"config": {"config_param": "stuff"}}}},
)

if __name__ == "__main__":
    # Will log "config_param: stuff"
    do_it_all_with_default_config.execute_in_process()
