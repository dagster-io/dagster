from dagster import job, op, resource


@resource
def external_service():
    ...


@op(required_resource_keys={"external_service"})
def do_something():
    ...


@job(resource_defs={"external_service": external_service})
def do_it_all():
    do_something()


# end_graph_with_resources

# start_execute_graph
def execute_graph_in_process():
    result = do_it_all_job.execute_in_process()
    assert result.output_for_node("do_something")


# end_execute_graph
