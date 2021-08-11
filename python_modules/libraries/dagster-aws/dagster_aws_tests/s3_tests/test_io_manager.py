from dagster import In, Int, Out, Output, VersionStrategy, job, op, resource
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.utils import construct_s3_client


def define_inty_job():
    @resource
    def test_s3_resource(_):
        return construct_s3_client(max_attempts=5)

    @op(out=Out(Int))
    def return_one():
        return 1

    @op(
        ins={"num": In(Int)},
        out=Out(Int),
    )
    def add_one(num):
        return num + 1

    @job(
        resource_defs={
            "io_manager": s3_pickle_io_manager,
            "s3": test_s3_resource,
        }
    )
    def basic_external_plan_execution():
        add_one(return_one())

    return basic_external_plan_execution


def test_s3_pickle_io_manager_execution(mock_s3_bucket):
    assert not len(list(mock_s3_bucket.objects.all()))
    inty_job = define_inty_job()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}

    result = inty_job.execute_in_process(run_config)

    assert result.output_for_node("return_one") == 1
    assert result.output_for_node("add_one") == 2

    assert len(list(mock_s3_bucket.objects.all())) == 2


def define_multiple_output_job():
    @resource
    def test_s3_resource(_):
        return construct_s3_client(max_attempts=5)

    @op(
        out={
            "foo": Out(Int),
            "foobar": Out(Int),
        }
    )
    def return_two_outputs():
        yield Output(10, "foobar")
        yield Output(5, "foo")

    @job(resource_defs={"io_manager": s3_pickle_io_manager, "s3": test_s3_resource})
    def output_prefix_execution_plan():
        return_two_outputs()

    return output_prefix_execution_plan


def test_s3_pickle_io_manager_prefix(mock_s3_bucket):
    assert not len(list(mock_s3_bucket.objects.all()))

    prefixy_job = define_multiple_output_job()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}

    result = prefixy_job.execute_in_process(run_config)

    assert result.output_for_node("return_two_outputs", "foo") == 5
    assert result.output_for_node("return_two_outputs", "foobar") == 10

    assert len(list(mock_s3_bucket.objects.all())) == 2


def test_memoization_s3_io_manager(mock_s3_bucket):
    class BasicVersionStrategy(VersionStrategy):
        def get_solid_version(self, solid_def):
            return "foo"

    @solid
    def basic_solid():
        return "foo"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"io_manager": s3_pickle_io_manager, "s3": s3_test_resource}
            )
        ],
        version_strategy=BasicVersionStrategy(),
    )
    def memoized_pipeline():
        basic_solid()

    run_config = {"resources": {"io_manager": {"config": {"s3_bucket": mock_s3_bucket.name}}}}
    with instance_for_test() as instance:
        result = execute_pipeline(memoized_pipeline, instance=instance, run_config=run_config)
        assert result.success
        assert result.output_for_solid("basic_solid") == "foo"

        result = execute_pipeline(memoized_pipeline, instance=instance, run_config=run_config)
        assert result.success
        assert len(result.step_event_list) == 0
