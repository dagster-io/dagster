import os
import pickle
import re

import pytest

from dagster import (
    DagsterEventType,
    DagsterExecutionStepNotFoundError,
    DependencyDefinition,
    Int,
    reconstructable,
)
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.instance import DagsterInstance
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.test_utils import default_mode_def_for_test, instance_for_test
from dagster._legacy import InputDefinition, OutputDefinition, PipelineDefinition, lambda_solid


def define_inty_pipeline(using_file_system=False):
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    @lambda_solid
    def user_throw_exception():
        raise Exception("whoops")

    pipeline = PipelineDefinition(
        name="basic_external_plan_execution",
        solid_defs=[return_one, add_one, user_throw_exception],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
        mode_defs=[default_mode_def_for_test] if using_file_system else None,
    )
    return pipeline


def define_reconstructable_inty_pipeline():
    return define_inty_pipeline(using_file_system=True)


def get_step_output(step_events, step_key, output_name="result"):
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def test_using_file_system_for_subplan():
    pipeline = define_inty_pipeline(using_file_system=True)

    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(pipeline)
    execution_plan = ExecutionPlan.build(InMemoryPipeline(pipeline), resolved_run_config)
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )
    assert execution_plan.get_step_by_key("return_one")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one"], pipeline, resolved_run_config),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    with open(
        os.path.join(instance.storage_directory(), pipeline_run.run_id, "return_one", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], pipeline, resolved_run_config),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one")
    with open(
        os.path.join(instance.storage_directory(), pipeline_run.run_id, "add_one", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 2


def test_using_file_system_for_subplan_multiprocessing():
    with instance_for_test() as instance:
        pipeline = reconstructable(define_reconstructable_inty_pipeline)

        resolved_run_config = ResolvedRunConfig.build(
            pipeline.get_definition(),
        )
        execution_plan = ExecutionPlan.build(
            pipeline,
            resolved_run_config,
        )
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(), execution_plan=execution_plan
        )

        assert execution_plan.get_step_by_key("return_one")

        return_one_step_events = list(
            execute_plan(
                execution_plan.build_subset_plan(
                    ["return_one"], pipeline.get_definition(), resolved_run_config
                ),
                pipeline,
                instance,
                run_config=dict(execution={"multiprocess": {}}),
                pipeline_run=pipeline_run,
            )
        )

        assert get_step_output(return_one_step_events, "return_one")
        with open(
            os.path.join(
                instance.storage_directory(),
                pipeline_run.run_id,
                "return_one",
                "result",
            ),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 1

        add_one_step_events = list(
            execute_plan(
                execution_plan.build_subset_plan(
                    ["add_one"], pipeline.get_definition(), resolved_run_config
                ),
                pipeline,
                instance,
                run_config=dict(execution={"multiprocess": {}}),
                pipeline_run=pipeline_run,
            )
        )

        assert get_step_output(add_one_step_events, "add_one")
        with open(
            os.path.join(instance.storage_directory(), pipeline_run.run_id, "add_one", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 2


def test_execute_step_wrong_step_key():
    pipeline = define_inty_pipeline()
    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(
        pipeline,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline),
        resolved_run_config,
    )
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(["nope.compute"], pipeline, resolved_run_config),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )

    assert exc_info.value.step_keys == ["nope.compute"]

    assert str(exc_info.value) == "Can not build subset plan from unknown step: nope.compute"

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(
                ["nope.compute", "nuh_uh.compute"], pipeline, resolved_run_config
            ),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )

    assert set(exc_info.value.step_keys) == {"nope.compute", "nuh_uh.compute"}

    assert re.match("Can not build subset plan from unknown steps", str(exc_info.value))


def test_using_file_system_for_subplan_missing_input():
    pipeline = define_inty_pipeline(using_file_system=True)

    instance = DagsterInstance.ephemeral()
    resolved_run_config = ResolvedRunConfig.build(
        pipeline,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline),
        resolved_run_config,
    )
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    events = execute_plan(
        execution_plan.build_subset_plan(["add_one"], pipeline, resolved_run_config),
        InMemoryPipeline(pipeline),
        instance,
        pipeline_run=pipeline_run,
    )
    failures = [event for event in events if event.event_type_value == "STEP_FAILURE"]
    assert len(failures) == 1
    assert failures[0].step_key == "add_one"
    assert "DagsterExecutionLoadInputError" in failures[0].event_specific_data.error.message


def test_using_file_system_for_subplan_invalid_step():
    pipeline = define_inty_pipeline(using_file_system=True)

    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(
        pipeline,
    )
    execution_plan = ExecutionPlan.build(
        InMemoryPipeline(pipeline),
        resolved_run_config,
    )

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline, execution_plan=execution_plan
    )

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(["nope.compute"], pipeline, resolved_run_config),
            InMemoryPipeline(pipeline),
            instance,
            pipeline_run=pipeline_run,
        )


import sys

from dagster import (
    AssetKey,
    AssetsDefinition,
    asset,
    define_asset_job,
    file_relative_path,
    op,
    repository,
)
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.repository_definition import AssetsDefinitionMetadata


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _metadata = AssetsDefinitionMetadata(keys_by_output_name={"result": AssetKey("foo")})

    def get_metadata(self):
        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "num_called"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})
        return [self._metadata]

    def get_definitions(self, metadata):
        assert len(metadata) == 1
        assert metadata == [self._metadata]

        @op
        def _op():
            return 1

        return [
            AssetsDefinition.from_op(_op, keys_by_output_name=md.keys_by_output_name)
            for md in metadata
        ]


@asset
def bar(foo):
    return foo + 1


@repository
def pending_repo():
    return [bar, MyCacheableAssetsDefinition("xyz"), define_asset_job("all_asset_job")]


def test_using_repository_data():
    records = []

    def event_callback(record):
        assert isinstance(record, EventLogEntry)
        records.append(record)

    from dagster._core.code_pointer import CodePointer
    from dagster._core.definitions.reconstruct import (
        ReconstructablePipeline,
        ReconstructableRepository,
    )
    from dagster._core.origin import PipelinePythonOrigin, RepositoryPythonOrigin

    with instance_for_test() as instance:
        repository_def = pending_repo.resolve(repository_metadata=None)
        pipeline_def = repository_def.get_job("all_asset_job")
        repository_metadata = repository_def.repository_metadata

        recon_repo = ReconstructableRepository.for_file(
            file_relative_path(__file__, "test_external_execution_plan.py"), fn_name="pending_repo"
        )
        recon_pipeline = ReconstructablePipeline(
            repository=recon_repo, pipeline_name="all_asset_job"
        ).with_repository_metadata(repository_metadata)

        # while create_execution_plan does support a repository_metadata argument, we cannot rely
        # on this being supplied by the caller in (e.g.) custom executors. In these cases, we rely
        # on the fact that the recon_pipeline will have been given repository metadata
        execution_plan = create_execution_plan(recon_pipeline)
        pipeline_run = instance.create_run_for_pipeline(
            pipeline_def=pipeline_def,
            execution_plan=execution_plan,
        )

        execute_plan(
            execution_plan=execution_plan,
            pipeline=recon_pipeline,
            pipeline_run=pipeline_run,
            instance=instance,
        )

        assert instance.run_storage.kvs_get({"num_called"}).get("num_called") == "1"
