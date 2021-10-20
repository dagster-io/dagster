from dagster import execute_pipeline, job, op, reconstructable
from dagster.core.test_utils import instance_for_test


def define_the_job():
    @op
    def my_op():
        return 5

    @job
    def call_the_op():
        for _ in range(10):
            my_op()

    return call_the_op


def test_job_execution_multiprocess_config():
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(define_the_job),
            instance=instance,
            run_config={"execution": {"config": {"max_concurrent": 4}}},
        )
        assert result.success
        assert result.output_for_solid("my_op") == 5
