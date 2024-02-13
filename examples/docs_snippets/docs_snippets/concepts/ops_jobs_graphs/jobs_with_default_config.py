from dagster import Config, OpExecutionContext, RunConfig, job, op


class DoSomethingConfig(Config):
    config_param: str


@op
def do_something(context: OpExecutionContext, config: DoSomethingConfig):
    context.log.info("config_param: " + config.config_param)


default_config = RunConfig(
    ops={"do_something": DoSomethingConfig(config_param="stuff")}
)


@job(config=default_config)
def do_it_all_with_default_config():
    do_something()


if __name__ == "__main__":
    # Will log "config_param: stuff"
    do_it_all_with_default_config.execute_in_process()
