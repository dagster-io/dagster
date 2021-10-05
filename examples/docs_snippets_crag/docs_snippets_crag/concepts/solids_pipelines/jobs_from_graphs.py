# start_define_graph
from dagster import ResourceDefinition, graph, op

prod_server = ResourceDefinition.mock_resource()
staging_server = ResourceDefinition.mock_resource()
local_server = ResourceDefinition.mock_resource()



@op(required_resource_keys={"server"})
def interact_with_server():
    ...


@graph
def do_stuff():
    interact_with_server()


# end_define_graph

# start_define_jobs
prod_job = do_stuff.to_job(name="do_stuff_prod", resource_defs={"server": prod_server})
staging_job = do_stuff.to_job(name="do_stuff_staging", resource_defs={"server": staging_server})
local_job = do_stuff.to_job(name="do_stuff_local", resource_defs={"local": local_server})
# end_define_jobs
