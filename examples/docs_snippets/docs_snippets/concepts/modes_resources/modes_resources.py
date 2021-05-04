from dagster import ModeDefinition, ResourceDefinition, execute_pipeline, pipeline, resource, solid
import requests
import csv

# start_solid_with_required_resource
@solid(required_resource_keys={"cereals_source"})
def load_cereals(context):
    lines = context.resource.fetch_cereal_lines()
    cereals = [row for row in csv.DictReader(lines)]
    context.log.info(f"Found {len(cereals)} cereals")


# end_solid_with_required_resource


# start_resource
class ExternalCerealsSource:
    def fetch_cereals_lines(self):
        response = requests.get("https://docs.dagster.io/assets/cereal.csv")
        return response.text.split("\n")


# end_resource

# start_pipeline
@pipeline(resource_defs={"cereals_source": ExternalCerealsSource()})
def cereal_pipeline():
    load_cereals()


# end_pipeline


# start_multiple_versions
class MockCerealsSource:
    def fetch_cereals_lines(self):
        response_text = """
        name,mfr,type,calories,protein,fat,sodium,fiber,carbo,sugars,potass,vitamins,shelf,weight,cups,rating
        100% Bran,N,C,70,4,1,130,10,5,6,280,25,3,1,0.33,68.402973
        100% Natural Bran,Q,C,120,3,5,15,2,8,8,135,0,3,1,1,33.983679
        """
        return response_text.split("\n")


@pipeline
def cereal_pipeline_2():
    load_cereals()


dev_pipeline = cereal_pipeline_2.bind({"cereals_source": MockCerealsSource()}, "dev")
prod_pipeline = cereal_pipeline_2.bind({"cereals_source": ExternalCerealsSource()}, "prod")


# end_multiple_versions


# start_repositories
from dagster import repository


@repository
def dev_repository():
    return [dev_pipeline]


@repository
def prod_repository():
    return [prod_pipeline]


# end_repositories

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
