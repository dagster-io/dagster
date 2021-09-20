from dagster import ConfigMapping, graph, op


@op(config_schema={"param": str})
def do_something(_):
    ...


@graph
def do_it_all():
    do_something()


# start
do_it_all_job = do_it_all.to_job(
    config=ConfigMapping(
        config_fn=lambda conf: {"solids": {"do_something": {"config": {"param": conf["arg"]}}}},
        config_schema={"arg": str},
    )
)
# end


def execute_do_it_all():
    # start_execute
    do_it_all_job.execute_in_process(run_config={"arg": "some_value"})
    # end_execute
