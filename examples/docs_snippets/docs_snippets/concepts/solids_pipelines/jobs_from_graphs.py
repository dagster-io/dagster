# isort: skip_file

# start_define_graph
from dagster import graph, op


@op(required_resource_keys={"server"})
def interact_with_server(context):
    context.resources.server.ping_server()


@graph
def do_stuff():
    interact_with_server()


# end_define_graph

# start_define_jobs
from dagster import ResourceDefinition

prod_server = ResourceDefinition.mock_resource()
local_server = ResourceDefinition.mock_resource()

prod_job = do_stuff.to_job(resource_defs={"server": prod_server}, name="do_stuff_prod")
local_job = do_stuff.to_job(
    resource_defs={"local": local_server}, name="do_stuff_local"
)
# end_define_jobs
