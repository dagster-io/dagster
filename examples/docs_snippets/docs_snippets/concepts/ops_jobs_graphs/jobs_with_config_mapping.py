from dagster import config_mapping, job, op


@op(config_schema={"config_param": str})
def do_something(context):
    context.log.info("config_param: " + context.op_config["config_param"])


@config_mapping(config_schema={"simplified_param": str})
def simplified_config(val):
    return {
        "ops": {"do_something": {"config": {"config_param": val["simplified_param"]}}}
    }


@job(config=simplified_config)
def do_it_all_with_simplified_config():
    do_something()


if __name__ == "__main__":
    # Will log "config_param: stuff"
    do_it_all_with_simplified_config.execute_in_process(
        run_config={"simplified_param": "stuff"}
    )
