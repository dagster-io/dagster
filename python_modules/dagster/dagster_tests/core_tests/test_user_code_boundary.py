from dagster import (
    String,
    dagster_type_loader,
    resource,
    usable_as_dagster_type,
)
from dagster._core.definitions.decorators import op
from dagster._core.definitions.input import In
from dagster._legacy import (
    ModeDefinition,
    execute_pipeline,
    pipeline,
)


class UserError(Exception):
    def __init__(self):
        super(UserError, self).__init__("The user has errored")


def test_user_error_boundary_solid_compute():
    @op
    def throws_user_error(_):
        raise UserError()

    @pipeline
    def pipeline_def():
        throws_user_error()

    pipeline_result = execute_pipeline(pipeline_def, raise_on_error=False)
    assert not pipeline_result.success


def test_user_error_boundary_input_hydration():
    @dagster_type_loader(String)
    def InputHydration(context, hello):
        raise UserError()

    @usable_as_dagster_type(loader=InputHydration)
    class CustomType(str):
        pass

    @op(ins={"custom_type": In(CustomType)})
    def input_hydration_solid(context, custom_type):
        context.log.info(custom_type)

    @pipeline
    def input_hydration_pipeline():
        input_hydration_solid()

    pipeline_result = execute_pipeline(
        input_hydration_pipeline,
        {"solids": {"input_hydration_solid": {"inputs": {"custom_type": "hello"}}}},
        raise_on_error=False,
    )
    assert not pipeline_result.success


def test_user_error_boundary_resource_init():
    @resource
    def resource_a(_):
        raise UserError()

    @op(required_resource_keys={"a"})
    def resource_solid(_context):
        return "hello"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
    def resource_pipeline():
        resource_solid()

    pipeline_result = execute_pipeline(resource_pipeline, raise_on_error=False)
    assert not pipeline_result.success
