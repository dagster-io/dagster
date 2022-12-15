from dagster import Definitions, job, op, sensor
from dagster._core.definitions.decorators.job_decorator import PendingJobDefinition
from dagster._core.definitions.run_request import SkipReason


def test_basic_pending_job():
    executed = {}

    @op(required_resource_keys={"a_resource"})
    def requires_resource(context):
        assert context.resources.a_resource == "foo"
        executed["yes"] = True
        return context.resources.a_resource + "returned"

    @job
    def a_pending_job():
        requires_resource()

    assert isinstance(a_pending_job, PendingJobDefinition)

    definitions = Definitions(jobs=[a_pending_job], resources={"a_resource": "foo"})

    result = definitions.get_job_def("a_pending_job").execute_in_process()
    assert result.success
    assert result.output_for_node("requires_resource") == "fooreturned"

    assert executed["yes"]


def test_pending_job_in_sensor():
    @op(required_resource_keys={"a_resource"})
    def requires_resource(context):
        pass

    @job
    def a_pending_job():
        requires_resource()

    @sensor(job=a_pending_job)
    def a_sensor():
        return SkipReason("always skip")

    definitions = Definitions(sensors=[a_sensor])

    result = definitions.get_job_def("a_pending_job").execute_in_process()
    assert result.success
