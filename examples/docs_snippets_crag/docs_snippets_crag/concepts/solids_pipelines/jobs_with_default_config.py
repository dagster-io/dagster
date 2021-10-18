from dagster import job, op


@op(config_schema={"config_param": str})
def do_something(context):
    context.log.info("config_param: " + context.op_config["config_param"])


default_config = {"ops": {"do_something": {"config": {"config_param": "stuff"}}}}


@job(config=default_config)
def do_it_all_with_default_config():
    do_something()


if __name__ == "__main__":
    # Will log "config_param: stuff"
    do_it_all_with_default_config.execute_in_process()
