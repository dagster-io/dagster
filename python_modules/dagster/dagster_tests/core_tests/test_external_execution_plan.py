import os
import pickle
import re
from typing import Optional, Sequence

import pytest
from dagster import (
    DagsterEventType,
    DagsterExecutionStepNotFoundError,
    DependencyDefinition,
    GraphDefinition,
    In,
    Int,
    Out,
    in_process_executor,
    mem_io_manager,
    op,
    reconstructable,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.reconstruct import ReconstructableJob, ReconstructableRepository
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance import DagsterInstance
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.test_utils import instance_for_test
from dagster._utils.test.definitions import lazy_definitions


def define_inty_job(using_file_system=False):
    @op
    def return_one():
        return 1

    @op(ins={"num": In(Int)}, out=Out(Int))
    def add_one(num):
        return num + 1

    @op
    def user_throw_exception():
        raise Exception("whoops")

    the_job = GraphDefinition(
        name="basic_external_plan_execution",
        node_defs=[return_one, add_one, user_throw_exception],
        dependencies={"add_one": {"num": DependencyDefinition("return_one")}},
    ).to_job(
        resource_defs=None if using_file_system else {"io_manager": mem_io_manager},
        executor_def=None if using_file_system else in_process_executor,
    )
    return the_job


def define_reconstructable_inty_job():
    return define_inty_job(using_file_system=True)


def get_step_output(
    step_events: Sequence[DagsterEvent], step_key: str, output_name: str = "result"
) -> Optional[DagsterEvent]:
    for step_event in step_events:
        if (
            step_event.event_type == DagsterEventType.STEP_OUTPUT
            and step_event.step_key == step_key
            and step_event.step_output_data.output_name == output_name
        ):
            return step_event
    return None


def test_using_file_system_for_subplan():
    foo_job = define_inty_job(using_file_system=True)

    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(foo_job)
    execution_plan = create_execution_plan(foo_job)
    run = instance.create_run_for_job(job_def=foo_job, execution_plan=execution_plan)
    assert execution_plan.get_step_by_key("return_one")

    return_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["return_one"], foo_job, resolved_run_config),
            InMemoryJob(foo_job),
            instance,
            dagster_run=run,
        )
    )

    assert get_step_output(return_one_step_events, "return_one")
    with open(
        os.path.join(instance.storage_directory(), run.run_id, "return_one", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 1

    add_one_step_events = list(
        execute_plan(
            execution_plan.build_subset_plan(["add_one"], foo_job, resolved_run_config),
            InMemoryJob(foo_job),
            instance,
            dagster_run=run,
        )
    )

    assert get_step_output(add_one_step_events, "add_one")
    with open(
        os.path.join(instance.storage_directory(), run.run_id, "add_one", "result"),
        "rb",
    ) as read_obj:
        assert pickle.load(read_obj) == 2


def test_using_file_system_for_subplan_multiprocessing():
    with instance_for_test() as instance:
        foo_job = reconstructable(define_reconstructable_inty_job)

        resolved_run_config = ResolvedRunConfig.build(
            foo_job.get_definition(),
        )

        execution_plan = create_execution_plan(
            foo_job,
        )
        run = instance.create_run_for_job(
            job_def=foo_job.get_definition(), execution_plan=execution_plan
        )

        assert execution_plan.get_step_by_key("return_one")

        return_one_step_events = list(
            execute_plan(
                execution_plan.build_subset_plan(
                    ["return_one"], foo_job.get_definition(), resolved_run_config
                ),
                foo_job,
                instance,
                run_config=dict(execution={"config": {"multiprocess": {}}}),
                dagster_run=run,
            )
        )

        assert get_step_output(return_one_step_events, "return_one")
        with open(
            os.path.join(
                instance.storage_directory(),
                run.run_id,
                "return_one",
                "result",
            ),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 1

        add_one_step_events = list(
            execute_plan(
                execution_plan.build_subset_plan(
                    ["add_one"], foo_job.get_definition(), resolved_run_config
                ),
                foo_job,
                instance,
                run_config=dict(execution={"config": {"multiprocess": {}}}),
                dagster_run=run,
            )
        )

        assert get_step_output(add_one_step_events, "add_one")
        with open(
            os.path.join(instance.storage_directory(), run.run_id, "add_one", "result"),
            "rb",
        ) as read_obj:
            assert pickle.load(read_obj) == 2


def test_execute_step_wrong_step_key():
    foo_job = define_inty_job()
    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(foo_job)
    execution_plan = create_execution_plan(foo_job)
    run = instance.create_run_for_job(job_def=foo_job, execution_plan=execution_plan)

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(["nope.compute"], foo_job, resolved_run_config),
            InMemoryJob(foo_job),
            instance,
            dagster_run=run,
        )

    assert exc_info.value.step_keys == ["nope.compute"]

    assert str(exc_info.value) == "Can not build subset plan from unknown step: nope.compute"

    with pytest.raises(DagsterExecutionStepNotFoundError) as exc_info:
        execute_plan(
            execution_plan.build_subset_plan(
                ["nope.compute", "nuh_uh.compute"], foo_job, resolved_run_config
            ),
            InMemoryJob(foo_job),
            instance,
            dagster_run=run,
        )

    assert set(exc_info.value.step_keys) == {"nope.compute", "nuh_uh.compute"}

    assert re.match("Can not build subset plan from unknown steps", str(exc_info.value))


def test_using_file_system_for_subplan_missing_input():
    foo_job = define_inty_job(using_file_system=True)

    instance = DagsterInstance.ephemeral()
    resolved_run_config = ResolvedRunConfig.build(foo_job)
    execution_plan = create_execution_plan(foo_job)
    run = instance.create_run_for_job(job_def=foo_job, execution_plan=execution_plan)

    events = execute_plan(
        execution_plan.build_subset_plan(["add_one"], foo_job, resolved_run_config),
        InMemoryJob(foo_job),
        instance,
        dagster_run=run,
    )
    failures = [event for event in events if event.event_type_value == "STEP_FAILURE"]
    assert len(failures) == 1
    assert failures[0].step_key == "add_one"
    assert "DagsterExecutionLoadInputError" in failures[0].event_specific_data.error.message


def test_using_file_system_for_subplan_invalid_step():
    foo_job = define_inty_job(using_file_system=True)

    instance = DagsterInstance.ephemeral()

    resolved_run_config = ResolvedRunConfig.build(foo_job)
    execution_plan = create_execution_plan(foo_job)

    run = instance.create_run_for_job(job_def=foo_job, execution_plan=execution_plan)

    with pytest.raises(DagsterExecutionStepNotFoundError):
        execute_plan(
            execution_plan.build_subset_plan(["nope.compute"], foo_job, resolved_run_config),
            InMemoryJob(foo_job),
            instance,
            dagster_run=run,
        )


def test_using_repository_data() -> None:
    with instance_for_test() as instance:
        # first, we resolve the repository to generate our cached metadata
        recon_repo = ReconstructableRepository.for_file(__file__, fn_name="cacheable_asset_defs")
        repo_def = recon_repo.get_definition()
        job_def = repo_def.get_job("all_asset_job")
        repository_load_data = repo_def.repository_load_data

        assert (
            instance.run_storage.get_cursor_values({"get_definitions_called"}).get(
                "get_definitions_called"
            )
            == "1"
        )

        recon_repo = ReconstructableRepository.for_file(__file__, fn_name="cacheable_asset_defs")
        recon_job = ReconstructableJob(repository=recon_repo, job_name="all_asset_job")

        execution_plan = create_execution_plan(recon_job, repository_load_data=repository_load_data)

        # need to get the definitions from metadata when creating the plan
        assert (
            instance.run_storage.get_cursor_values({"get_definitions_called"}).get(
                "get_definitions_called"
            )
            == "2"
        )

        run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)

        execute_plan(
            execution_plan=execution_plan,
            job=recon_job,
            dagster_run=run,
            instance=instance,
        )

        assert (
            instance.run_storage.get_cursor_values({"compute_cacheable_data_called"}).get(
                "compute_cacheable_data_called"
            )
            == "1"
        )
        # should not have needed to get_definitions again after creating the plan
        assert (
            instance.run_storage.get_cursor_values({"get_definitions_called"}).get(
                "get_definitions_called"
            )
            == "2"
        )


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cacheable_data = AssetsDefinitionCacheableData(
        keys_by_output_name={"result": AssetKey("foo")},
        metadata_by_output_name={
            "result": {
                "some_val": MetadataValue.table_schema(
                    schema=TableSchema(columns=[TableColumn("some_col")])
                )
            }
        },
    )

    def compute_cacheable_data(self):
        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "compute_cacheable_data_called"
        compute_cacheable_data_called = int(
            instance.run_storage.get_cursor_values({kvs_key}).get(kvs_key, "0")
        )
        instance.run_storage.set_cursor_values({kvs_key: str(compute_cacheable_data_called + 1)})
        # Skip the tracking if this is called outside the context of a DagsterInstance
        return [self._cacheable_data]

    def build_definitions(self, data):
        assert len(data) == 1
        assert data == [self._cacheable_data]

        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "get_definitions_called"
        get_definitions_called = int(
            instance.run_storage.get_cursor_values({kvs_key}).get(kvs_key, "0")
        )
        instance.run_storage.set_cursor_values({kvs_key: str(get_definitions_called + 1)})

        @op
        def _op():
            return 1

        return [
            AssetsDefinition.from_op(_op, keys_by_output_name=cd.keys_by_output_name) for cd in data
        ]


@lazy_definitions
def cacheable_asset_defs():
    @asset
    def bar(foo):
        return foo + 1

    return Definitions(
        assets=[bar, MyCacheableAssetsDefinition("xyz")],
        jobs=[define_asset_job("all_asset_job")],
    )
