# start_graph_with_resources
from dagster import graph, op, resource


@resource
def external_service():
    ...


@op(required_resource_keys={"external_service"})
def do_something():
    ...


@graph
def do_it_all():
    do_something()


do_it_all_job = do_it_all.to_job(resource_defs={"external_service": external_service})
# end_graph_with_resources

# start_execute_graph
def execute_graph_in_process():
    result = do_it_all_job.execute_in_process()
    assert result.output_for_node("do_something")


# end_execute_graph
