# ruff: isort: skip_file

# start_define_graph
import dagster as dg


class Server(dg.ConfigurableResource):
    def ping_server(self): ...


@dg.op
def interact_with_server(server: Server):
    server.ping_server()


@dg.graph
def do_stuff():
    interact_with_server()


# end_define_graph

# start_define_jobs
import dagster as dg

prod_server = dg.ResourceDefinition.mock_resource()
local_server = dg.ResourceDefinition.mock_resource()

prod_job = do_stuff.to_job(resource_defs={"server": prod_server}, name="do_stuff_prod")
local_job = do_stuff.to_job(
    resource_defs={"server": local_server}, name="do_stuff_local"
)
# end_define_jobs
