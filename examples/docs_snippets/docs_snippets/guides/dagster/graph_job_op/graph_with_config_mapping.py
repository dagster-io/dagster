from dagster import config_mapping, job, op


@op(config_schema={"param": str})
def do_something(_):
    ...


# start


@config_mapping(config_schema={"arg": str})
def my_config_mapping(conf):
    return {"solids": {"do_something": {"config": {"param": conf["arg"]}}}}


@job(config=my_config_mapping)
def do_it_all():
    do_something()


# end


def execute_do_it_all():
    # start_execute
    do_it_all.execute_in_process(run_config={"arg": "some_value"})
    # end_execute
