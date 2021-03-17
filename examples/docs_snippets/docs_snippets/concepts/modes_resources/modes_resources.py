# pylint: disable=unused-argument
from dagster import ModeDefinition, ResourceDefinition, execute_pipeline, pipeline, resource, solid


# start_resource_example
class ExternalCerealFetcher:
    def fetch_new_cereals(self, start_ts, end_ts):
        pass


@resource
def cereal_fetcher(init_context):
    return ExternalCerealFetcher()


# end_resource_example

resource_a = ResourceDefinition.hardcoded_resource(1)
resource_b = ResourceDefinition.hardcoded_resource(2)

# start_mode_example
mode_def_ab = ModeDefinition(
    "ab_mode",
    resource_defs={
        "a": resource_a,
        "b": resource_b,
    },
)
# end_mode_example

mode_def_c = ModeDefinition("c_mode", resource_defs={"a": resource_a})


@solid(required_resource_keys={"a"})
def basic_solid(_):
    pass


# start_pipeline_example
@pipeline(mode_defs=[mode_def_ab, mode_def_c])
def pipeline_with_mode():
    basic_solid()


# end_pipeline_example

# start_execute_example
execute_pipeline(pipeline_with_mode, mode="ab_mode")
# end_execute_example

# start_resource_dep_example
@resource
def foo_resource(_):
    return "foo"


@resource(required_resource_keys={"foo"})
def emit_foo(init_context):
    return init_context.resources.foo


# end_resource_dep_example

# start_resource_dep_mode
ModeDefinition(resource_defs={"foo": foo_resource, "emit": emit_foo})
# end_resource_dep_mode

# start_resource_config
class DatabaseConnection:
    def __init__(self, connection: str):
        self.connection = connection


@resource(config_schema={"connection": str})
def db_resource(init_context):
    connection = init_context.resource_config["connection"]
    return DatabaseConnection(connection)


# end_resource_config
