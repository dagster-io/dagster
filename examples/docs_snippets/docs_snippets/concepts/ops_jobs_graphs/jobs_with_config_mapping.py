from dagster import Config, OpExecutionContext, RunConfig, config_mapping, job, op


class DoSomethingConfig(Config):
    config_param: str


@op
def do_something(context: OpExecutionContext, config: DoSomethingConfig) -> None:
    context.log.info("config_param: " + config.config_param)


class SimplifiedConfig(Config):
    simplified_param: str


@config_mapping
def simplified_config(val: SimplifiedConfig) -> RunConfig:
    return RunConfig(
        ops={"do_something": DoSomethingConfig(config_param=val.simplified_param)}
    )


@job(config=simplified_config)
def do_it_all_with_simplified_config():
    do_something()


if __name__ == "__main__":
    # Will log "config_param: stuff"
    do_it_all_with_simplified_config.execute_in_process(
        run_config={"simplified_param": "stuff"}
    )
