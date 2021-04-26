import os

from dagster import ModeDefinition, executor, pipeline, reconstructable, resource, solid
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.host_mode import execute_run_host_mode
from dagster.core.execution.retries import RetryMode
from dagster.core.executor.multiprocess import MultiprocessExecutor
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test


@resource
def add_one_resource(_):
    def add_one(num):
        return num + 1

    return add_one


@resource
def add_two_resource(_):
    def add_two(num):
        return num + 2

    return add_two


@solid(required_resource_keys={"adder"})
def solid_that_uses_adder_resource(context, number):
    return context.resources.adder(number)


@pipeline(
    mode_defs=[
        ModeDefinition(name="add_one", resource_defs={"adder": add_one_resource}),
        ModeDefinition(name="add_two", resource_defs={"adder": add_two_resource}),
    ]
)
def pipeline_with_mode():
    solid_that_uses_adder_resource()


_explode_pid = {"pid": None}

# Will throw if the run worker pid tries to access the definition, but subprocesses (the step
# workers) can access the definition
class ExplodingTestPipeline(ReconstructablePipeline):
    def __new__(
        cls,
        repository,
        pipeline_name,
        solid_selection_str=None,
        solids_to_execute=None,
    ):  # pylint: disable=signature-differs
        return super(ExplodingTestPipeline, cls).__new__(
            cls,
            repository,
            pipeline_name,
            solid_selection_str,
            solids_to_execute,
        )

    def get_definition(self):
        if os.getpid() == _explode_pid["pid"]:
            raise Exception("Got the definition in the run worker process")
        return super(ExplodingTestPipeline, self).get_definition()


def test_host_run_worker():
    _explode_pid["pid"] = os.getpid()

    with instance_for_test() as instance:
        run_config = {
            "solids": {"solid_that_uses_adder_resource": {"inputs": {"number": {"value": 4}}}},
            "intermediate_storage": {"filesystem": {}},
            "execution": {"multiprocess": {}},
        }
        execution_plan = create_execution_plan(
            pipeline_with_mode,
            run_config,
        )

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_with_mode,
            execution_plan=execution_plan,
            run_config=run_config,
        )

        recon_pipeline = reconstructable(pipeline_with_mode)

        execute_run_host_mode(
            ExplodingTestPipeline(recon_pipeline.repository, recon_pipeline.pipeline_name),
            pipeline_run,
            instance,
            raise_on_error=True,
        )

        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS

        logs = instance.all_logs(pipeline_run.run_id)
        assert any(
            e.is_dagster_event and "Executing steps using multiprocess executor" in e.message
            for e in logs
        )


@executor(
    name="custom_test_executor",
    config_schema={},
)
def test_executor(_init_context):
    return MultiprocessExecutor(max_concurrent=4, retries=RetryMode.DISABLED)


def _custom_get_executor_def_fn(executor_name):
    assert not executor_name
    return test_executor


def test_custom_executor_fn():
    _explode_pid["pid"] = os.getpid()

    with instance_for_test() as instance:
        run_config = {
            "solids": {"solid_that_uses_adder_resource": {"inputs": {"number": {"value": 4}}}},
            "intermediate_storage": {"filesystem": {}},
        }
        execution_plan = create_execution_plan(
            pipeline_with_mode,
            run_config,
        )

        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_with_mode,
            execution_plan=execution_plan,
            run_config=run_config,
        )

        recon_pipeline = reconstructable(pipeline_with_mode)

        execute_run_host_mode(
            ExplodingTestPipeline(recon_pipeline.repository, recon_pipeline.pipeline_name),
            pipeline_run,
            instance,
            get_executor_def_fn=_custom_get_executor_def_fn,
            raise_on_error=True,
        )

        assert instance.get_run_by_id(pipeline_run.run_id).status == PipelineRunStatus.SUCCESS

        logs = instance.all_logs(pipeline_run.run_id)
        assert any(
            e.is_dagster_event and "Executing steps using multiprocess executor" in e.message
            for e in logs
        )
