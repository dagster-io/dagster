from dagster import (
    In,
    Out,
    String,
    dagster_type_loader,
    dagster_type_materializer,
    job,
    op,
    resource,
    usable_as_dagster_type,
)
from dagster._core.types.dagster_type import create_any_type


class UserError(Exception):
    def __init__(self):
        super(UserError, self).__init__("The user has errored")


def test_user_error_boundary_solid_compute():
    @op
    def throws_user_error(_):
        raise UserError()

    @job
    def job_def():
        throws_user_error()

    pipeline_result = job_def.execute_in_process(raise_on_error=False)
    assert not pipeline_result.success


def test_user_error_boundary_input_hydration():
    @dagster_type_loader(String)
    def InputHydration(context, hello):
        raise UserError()

    @usable_as_dagster_type(loader=InputHydration)
    class CustomType(str):
        pass

    @op(ins={"custom_type": In(CustomType)})
    def input_hydration_op(context, custom_type):
        context.log.info(custom_type)

    @job
    def input_hydration_job():
        input_hydration_op()

    pipeline_result = input_hydration_job.execute_in_process(
        {"solids": {"input_hydration_op": {"inputs": {"custom_type": "hello"}}}},
        raise_on_error=False,
    )
    assert not pipeline_result.success


def test_user_error_boundary_output_materialization():
    @dagster_type_materializer(String)
    def materialize(context, *_args, **_kwargs):
        raise UserError()

    CustomDagsterType = create_any_type(name="CustomType", materializer=materialize)

    @op(out=Out(CustomDagsterType))
    def output_op(_context):
        return "hello"

    @job
    def output_materialization_job():
        output_op()

    pipeline_result = output_materialization_job.execute_in_process(
        {"solids": {"output_op": {"outputs": [{"result": "hello"}]}}},
        raise_on_error=False,
    )
    assert not pipeline_result.success


def test_user_error_boundary_resource_init():
    @resource
    def resource_a(_):
        raise UserError()

    @op(required_resource_keys={"a"})
    def resource_op(_context):
        return "hello"

    @job(resource_defs={"a": resource_a})
    def resource_job():
        resource_op()

    pipeline_result = resource_job.execute_in_process(raise_on_error=False)
    assert not pipeline_result.success
