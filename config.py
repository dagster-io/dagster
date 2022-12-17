from dagster import Resource, EnvVar, UIValue, Config
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.definitions_class import Definitions



class Foo(Resource):
    bar: str
    foo: int
    baaz: str


Definitions(
    resources={
        "a_resource": Foo(
            baaz="a value ", ## --force?
            bar=EnvVar("FOOBAR"),
            foo=DagsterCloudValue(default="dlkjfd"),
        )
    }
)

class Bar(Config):
    value: str


Bar(value=EnvVar("machine_type"))

@asset
def an_asset(config: Bar):
    pass


# Use cases
# Run config thing
# Vinnie thing
# Yaml thing

# We think of it as definition time versus runtime time
# In our users mind it is between python land and yaml land

# Input data points
# 1) When we didn't have config it was a blocker
# 2) The Vinnie thing. Definition. He has a set of assets and each asset has a straightforward knobs that he wants to be set in yaml and then observable in dagit
# 3) Prezi. They were heavy users of the config system but they did everything at definition time.


# def produce_an_op(config: Bar):
#     @op
#     def an_op():
#         config.bar
