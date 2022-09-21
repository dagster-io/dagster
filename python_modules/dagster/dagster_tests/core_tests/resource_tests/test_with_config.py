from distutils.command.config import config
from importlib.resources import Resource
from re import A
from dagster import resource, op, job, ResourceDefinition
from dagster._core.definitions.resource_definition import typed_resource_ctor

@resource(config_schema={"database": str})
def configurable_some_resource(init_context):
    return dict(database=init_context.resource_config["database"])

@typed_resource_ctor(configurable_some_resource)
def some_resource(database: str):
    return configurable_some_resource.configured({"database": database})

def test_typed_some_resource():
    configured_inst = some_resource.configured({"database": "foo"})
    assert isinstance(configured_inst, ResourceDefinition)

    typed_inst = some_resource(database="bar")
    assert isinstance(typed_inst, ResourceDefinition)

    @op(required_resource_keys={'some_resource'})
    def use_some_resource(context):
        return context.resources.some_resource

    @job(resource_defs={'some_resource': configured_inst})
    def configured_job():
        use_some_resource()

    assert configured_job.execute_in_process().output_for_node("use_some_resource") == {"database": "foo"}

    @job(resource_defs={'some_resource': typed_inst})
    def inst_job():
        use_some_resource()

    assert inst_job.execute_in_process().output_for_node("use_some_resource") == {"database": "bar"}

    @job(resource_defs={'some_resource': some_resource})
    def trad_job():
        use_some_resource()
    
    assert trad_job.execute_in_process(
        run_config={'resources': {'some_resource': {'config': {'database': 'baaz'}}}}).output_for_node("use_some_resource") == {"database": "baaz"}
