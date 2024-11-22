from dagster import In, String, dagster_type_loader, job, op, resource, usable_as_dagster_type


class UserError(Exception):
    def __init__(self):
        super().__init__("The user has errored")


def test_user_error_boundary_op_compute():
    @op
    def throws_user_error(_):
        raise UserError()

    @job
    def job_def():
        throws_user_error()

    result = job_def.execute_in_process(raise_on_error=False)
    assert not result.success


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

    result = input_hydration_job.execute_in_process(
        {"ops": {"input_hydration_op": {"inputs": {"custom_type": "hello"}}}},
        raise_on_error=False,
    )
    assert not result.success


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

    result = resource_job.execute_in_process(raise_on_error=False)
    assert not result.success
