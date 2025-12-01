import re
import traceback
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from unittest.mock import Mock

import dagster as dg
import pytest
from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    Definitions,
    ResourceDefinition,
    in_process_executor,
    multiprocess_executor,
)
from dagster._check import CheckError
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET,
)
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.partitions.context import PartitionLoadingContext
from dagster._core.types.pagination import PaginatedResults
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.core.component_tree import ComponentTree
from dagster_shared.error import SerializableErrorInfo
from toposort import CircularDependencyError


def get_all_assets_from_defs(defs: Definitions):
    return list(defs.get_repository_def().asset_graph.assets_defs)


def test_basic_asset():
    assert dg.Definitions

    @dg.asset
    def an_asset():
        pass

    defs = dg.Definitions(assets=[an_asset])

    all_assets = get_all_assets_from_defs(defs)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "an_asset"


def test_basic_asset_job_definition():
    @dg.asset
    def an_asset():
        pass

    defs = dg.Definitions(assets=[an_asset], jobs=[dg.define_asset_job(name="an_asset_job")])

    assert isinstance(defs.resolve_job_def("an_asset_job"), dg.JobDefinition)


def test_vanilla_job_definition():
    @dg.op
    def an_op():
        pass

    @dg.job
    def a_job():
        pass

    defs = dg.Definitions(jobs=[a_job])
    assert isinstance(defs.resolve_job_def("a_job"), dg.JobDefinition)


def test_basic_schedule_definition():
    @dg.asset
    def an_asset():
        pass

    defs = dg.Definitions(
        assets=[an_asset],
        schedules=[
            dg.ScheduleDefinition(
                name="daily_an_asset_schedule",
                job=dg.define_asset_job(name="an_asset_job"),
                cron_schedule="@daily",
            )
        ],
    )

    assert defs.resolve_schedule_def("daily_an_asset_schedule")


def test_basic_sensor_definition():
    @dg.asset
    def an_asset():
        pass

    an_asset_job = dg.define_asset_job(name="an_asset_job")

    @dg.sensor(name="an_asset_sensor", job=an_asset_job)
    def a_sensor():
        raise NotImplementedError()

    defs = dg.Definitions(
        assets=[an_asset],
        sensors=[a_sensor],
    )

    assert defs.resolve_sensor_def("an_asset_sensor")


def test_with_resource_binding():
    executed = {}

    @dg.asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "wrapped"
        executed["yes"] = True

    defs = dg.Definitions(
        assets=[requires_foo],
        resources={"foo": ResourceDefinition.hardcoded_resource("wrapped")},
    )
    repo = defs.get_repository_def()

    assert len(repo.get_top_level_resources()) == 1
    assert "foo" in repo.get_top_level_resources()

    asset_job = repo.get_all_jobs()[0]
    asset_job.execute_in_process()
    assert executed["yes"]


def test_nested_resources() -> None:
    class MyInnerResource(dg.ConfigurableResource):
        a_str: str

    class MyOuterResource(dg.ConfigurableResource):
        inner: MyInnerResource

    inner = MyInnerResource(a_str="wrapped")
    defs = dg.Definitions(
        resources={"foo": MyOuterResource(inner=inner)},
    )
    repo = defs.get_repository_def()

    assert len(repo.get_top_level_resources()) == 1
    assert "foo" in repo.get_top_level_resources()


def test_resource_coercion():
    executed = {}

    @dg.asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "object-to-coerce"
        executed["yes"] = True

    defs = dg.Definitions(
        assets=[requires_foo],
        resources={"foo": "object-to-coerce"},
    )
    repo = defs.get_repository_def()

    assert len(repo.get_top_level_resources()) == 1
    assert "foo" in repo.get_top_level_resources()

    asset_job = repo.get_all_jobs()[0]
    asset_job.execute_in_process()
    assert executed["yes"]


def test_source_asset():
    defs = dg.Definitions(assets=[dg.SourceAsset("a-source-asset")])
    repo = defs.get_repository_def()
    all_assets = list(repo.asset_graph.assets_defs)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "a-source-asset"


def test_cacheable_asset_repo():
    class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={},
                    keys_by_output_name={"result": dg.AssetKey(self.unique_id)},
                )
            ]

        def build_definitions(self, data):
            @dg.op
            def my_op():
                return 1

            return [
                AssetsDefinition.from_op(
                    my_op,
                    keys_by_input_name=cd.keys_by_input_name,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    # now actually test definitions

    with scoped_definitions_load_context():
        defs = dg.Definitions(assets=[MyCacheableAssetsDefinition("foobar")])
        all_assets = get_all_assets_from_defs(defs)
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "foobar"

        assert isinstance(defs.resolve_implicit_global_asset_job_def(), dg.JobDefinition)


def test_asset_loading():
    @dg.asset
    def one():
        return 1

    @dg.asset
    def two():
        return 2

    with dg.instance_for_test() as instance:
        defs = dg.Definitions(assets=[one, two])
        dg.materialize(assets=[one, two], instance=instance)
        assert defs.load_asset_value("one", instance=instance) == 1
        assert defs.load_asset_value("two", instance=instance) == 2

        value_loader = defs.get_asset_value_loader(instance)
        assert value_loader.load_asset_value("one") == 1
        assert value_loader.load_asset_value("two") == 2


def test_io_manager_coercion():
    @dg.asset(io_manager_key="mem_io_manager")
    def one():
        return 1

    defs = dg.Definitions(assets=[one], resources={"mem_io_manager": dg.InMemoryIOManager()})

    asset_job = defs.resolve_implicit_global_asset_job_def()
    assert isinstance(asset_job.resource_defs["mem_io_manager"], dg.IOManagerDefinition)
    result = asset_job.execute_in_process()
    assert result.output_for_node("one") == 1


def test_bad_executor():
    with pytest.raises(CheckError):
        # ignoring type to catch runtime error
        dg.Definitions(executor="not an executor")  # pyright: ignore[reportArgumentType]


def test_custom_executor_in_definitions():
    @dg.executor
    def an_executor(_):
        raise Exception("not executed")

    @dg.asset
    def one():
        return 1

    defs = dg.Definitions(assets=[one], executor=an_executor)
    asset_job = defs.resolve_implicit_global_asset_job_def()
    assert asset_job.executor_def is an_executor


def test_custom_loggers_in_definitions():
    @dg.logger
    def a_logger(_):
        raise Exception("not executed")

    @dg.asset
    def one():
        return 1

    defs = dg.Definitions(assets=[one], loggers={"custom_logger": a_logger})

    asset_job = defs.resolve_implicit_global_asset_job_def()
    loggers = asset_job.loggers
    assert len(loggers) == 1
    assert "custom_logger" in loggers
    assert loggers["custom_logger"] is a_logger


def test_bad_logger_key():
    @dg.logger
    def a_logger(_):
        raise Exception("not executed")

    with pytest.raises(CheckError):
        # ignore type to catch runtime error
        dg.Definitions(loggers={1: a_logger})  # pyright: ignore[reportArgumentType]


def test_bad_logger_value():
    with pytest.raises(CheckError):
        # ignore type to catch runtime error
        dg.Definitions(loggers={"not_a_logger": "not_a_logger"})  # pyright: ignore[reportArgumentType]


def test_kitchen_sink_on_create_helper_and_definitions():
    @dg.asset(required_resource_keys={"a_resource_key"})
    def an_asset():
        pass

    @dg.asset
    def another_asset():
        pass

    @dg.asset_check(asset=an_asset)
    def a_check():
        return dg.AssetCheckResult(passed=True)

    another_asset_job = dg.define_asset_job(name="another_asset_job", selection="another_asset")

    @dg.op
    def an_op():
        pass

    @dg.op(required_resource_keys={"a_resource_key"})
    def other_op():
        pass

    @dg.job
    def a_job():
        an_op()

    @dg.job
    def sensor_target():
        other_op()

    @dg.job
    def schedule_target():
        an_op()

    a_schedule = dg.ScheduleDefinition(
        name="a_schedule", job=schedule_target, cron_schedule="@daily"
    )

    @dg.sensor(job=sensor_target)
    def a_sensor(_):
        raise Exception("not called")

    @dg.executor
    def an_executor(_):
        raise Exception("not executed")

    @dg.logger
    def a_logger(_):
        raise Exception("not executed")

    repo = dg.create_repository_using_definitions_args(
        name="foobar",
        assets=[an_asset, another_asset],
        jobs=[
            a_job,
            another_asset_job,
            sensor_target,
            schedule_target,
        ],
        schedules=[a_schedule],
        sensors=[a_sensor],
        resources={"a_resource_key": "the resource"},
        executor=an_executor,
        loggers={"logger_key": a_logger},
        asset_checks=[a_check],
    )

    assert isinstance(repo, dg.RepositoryDefinition)

    assert repo.name == "foobar"
    assert isinstance(repo.get_job("a_job"), dg.JobDefinition)
    assert repo.get_job("a_job").executor_def is an_executor
    assert repo.get_job("a_job").loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_implicit_global_asset_job_def(), dg.JobDefinition)
    assert repo.get_implicit_global_asset_job_def().executor_def is an_executor
    assert repo.get_implicit_global_asset_job_def().loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_job("another_asset_job"), dg.JobDefinition)
    assert repo.get_job("another_asset_job").executor_def is an_executor
    assert repo.get_job("another_asset_job").loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_job("sensor_target"), dg.JobDefinition)
    assert repo.get_job("sensor_target").executor_def is an_executor
    assert repo.get_job("sensor_target").loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_job("schedule_target"), dg.JobDefinition)
    assert repo.get_job("schedule_target").executor_def is an_executor
    assert repo.get_job("schedule_target").loggers == {"logger_key": a_logger}

    assert isinstance(repo.get_schedule_def("a_schedule"), dg.ScheduleDefinition)
    assert isinstance(repo.get_sensor_def("a_sensor"), dg.SensorDefinition)

    # test the kitchen sink since we have created it
    defs = dg.Definitions(
        assets=[an_asset, another_asset],
        jobs=[
            a_job,
            another_asset_job,
            sensor_target,
            schedule_target,
        ],
        schedules=[a_schedule],
        sensors=[a_sensor],
        resources={"a_resource_key": "the resource"},
        executor=an_executor,
        loggers={"logger_key": a_logger},
        asset_checks=[a_check],
    )

    assert isinstance(defs.resolve_job_def("a_job"), dg.JobDefinition)
    assert defs.resolve_job_def("a_job").executor_def is an_executor
    assert defs.resolve_job_def("a_job").loggers == {"logger_key": a_logger}
    assert isinstance(defs.resolve_implicit_global_asset_job_def(), dg.JobDefinition)
    assert defs.resolve_implicit_global_asset_job_def().executor_def is an_executor
    assert defs.resolve_implicit_global_asset_job_def().loggers == {"logger_key": a_logger}
    assert isinstance(defs.resolve_job_def("another_asset_job"), dg.JobDefinition)
    assert defs.resolve_job_def("another_asset_job").executor_def is an_executor
    assert defs.resolve_job_def("another_asset_job").loggers == {"logger_key": a_logger}
    assert isinstance(defs.resolve_job_def("sensor_target"), dg.JobDefinition)
    assert defs.resolve_job_def("sensor_target").executor_def is an_executor
    assert defs.resolve_job_def("sensor_target").loggers == {"logger_key": a_logger}
    assert isinstance(defs.resolve_job_def("schedule_target"), dg.JobDefinition)
    assert defs.resolve_job_def("schedule_target").executor_def is an_executor
    assert defs.resolve_job_def("schedule_target").loggers == {"logger_key": a_logger}

    assert isinstance(defs.resolve_schedule_def("a_schedule"), dg.ScheduleDefinition)
    assert isinstance(defs.resolve_sensor_def("a_sensor"), dg.SensorDefinition)

    def _update(metadata):
        return {**metadata, "new": "value"}

    updated_defs = defs.with_definition_metadata_update(_update)
    assert updated_defs.resolve_schedule_def("a_schedule").metadata["new"] == dg.TextMetadataValue(
        "value"
    )
    assert updated_defs.resolve_sensor_def("a_sensor").metadata["new"] == dg.TextMetadataValue(
        "value"
    )
    assert updated_defs.resolve_job_def("a_job").metadata["new"] == dg.TextMetadataValue("value")

    updated_graph = updated_defs.resolve_asset_graph()
    for assets_def in updated_graph.assets_defs:
        for metadata in assets_def.metadata_by_key.values():
            assert metadata["new"] == "value"

    assert updated_graph.get_check_spec(a_check.check_key).metadata["new"] == "value"


def test_with_resources_override():
    executed = {}

    @dg.asset(required_resource_keys={"a_resource"})
    def asset_one(context):
        executed["asset_one"] = True
        assert context.resources.a_resource == "passed-through-with-resources"

    @dg.asset(required_resource_keys={"b_resource"})
    def asset_two(context):
        executed["asset_two"] = True
        assert context.resources.b_resource == "passed-through-definitions"

    defs = dg.Definitions(
        assets=[
            *dg.with_resources(
                [asset_one],
                {
                    "a_resource": ResourceDefinition.hardcoded_resource(
                        "passed-through-with-resources"
                    )
                },
            ),
            asset_two,
        ],
        resources={"b_resource": "passed-through-definitions"},
    )

    defs.resolve_implicit_global_asset_job_def().execute_in_process()

    assert executed["asset_one"]
    assert executed["asset_two"]


def test_implicit_global_job():
    @dg.asset
    def asset_one():
        pass

    defs = dg.Definitions(assets=[asset_one])

    assert defs.has_implicit_global_asset_job_def()
    assert len(defs.resolve_all_job_defs()) == 1


def test_implicit_global_job_with_job_defined():
    @dg.asset
    def asset_one():
        pass

    defs = dg.Definitions(
        assets=[asset_one], jobs=[dg.define_asset_job("all_assets_job", selection="*")]
    )

    assert defs.has_implicit_global_asset_job_def()
    assert defs.resolve_job_def("all_assets_job")
    assert (
        defs.resolve_job_def("all_assets_job") is not defs.resolve_implicit_global_asset_job_def()
    )

    assert len(defs.resolve_all_job_defs()) == 2


def test_implicit_global_job_with_partitioned_asset():
    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def daily_partition_asset(context: AssetExecutionContext):
        return context.partition_key

    @dg.asset(partitions_def=dg.HourlyPartitionsDefinition(start_date="2022-02-02-10:00"))
    def hourly_partition_asset(context: AssetExecutionContext):
        return context.partition_key

    @dg.asset
    def unpartitioned_asset():
        pass

    defs = dg.Definitions(
        assets=[daily_partition_asset, unpartitioned_asset, hourly_partition_asset],
    )

    assert len(defs.resolve_all_job_defs()) == 1
    defs.resolve_implicit_global_asset_job_def()


def test_implicit_job_with_source_assets():
    source_asset = dg.SourceAsset("source_asset")

    @dg.asset
    def downstream_of_source(source_asset):
        raise Exception("not executed")

    defs = dg.Definitions(assets=[source_asset, downstream_of_source])
    assert defs.resolve_all_job_defs()
    assert len(defs.resolve_all_job_defs()) == 1
    assert defs.resolve_implicit_job_def_def_for_assets(
        asset_keys=[dg.AssetKey("downstream_of_source")]
    )
    assert defs.has_implicit_global_asset_job_def()
    assert defs.resolve_implicit_global_asset_job_def()


def test_unresolved_partitioned_asset_schedule():
    partitions_def = dg.DailyPartitionsDefinition(start_date="2020-01-01")

    @dg.asset(partitions_def=partitions_def)
    def asset1(): ...

    job1 = dg.define_asset_job("job1")
    schedule1 = dg.build_schedule_from_partitioned_job(job1)

    defs_with_explicit_job = dg.Definitions(jobs=[job1], schedules=[schedule1], assets=[asset1])
    assert defs_with_explicit_job.resolve_job_def("job1").name == "job1"
    assert defs_with_explicit_job.resolve_job_def("job1").partitions_def == partitions_def
    assert defs_with_explicit_job.resolve_schedule_def("job1_schedule").cron_schedule == "0 0 * * *"

    defs_with_implicit_job = dg.Definitions(schedules=[schedule1], assets=[asset1])
    assert defs_with_implicit_job.resolve_job_def("job1").name == "job1"
    assert defs_with_implicit_job.resolve_job_def("job1").partitions_def == partitions_def
    assert defs_with_implicit_job.resolve_schedule_def("job1_schedule").cron_schedule == "0 0 * * *"


def test_bare_executor():
    @dg.asset
    def an_asset(): ...

    class DummyExecutor(dg.Executor):
        def execute(self, plan_context, execution_plan): ...  # pyright: ignore[reportIncompatibleMethodOverride]

        @property
        def retries(self): ...  # pyright: ignore[reportIncompatibleMethodOverride]

    executor_inst = DummyExecutor()

    defs = dg.Definitions(assets=[an_asset], executor=executor_inst)

    job = defs.resolve_implicit_global_asset_job_def()
    assert isinstance(job, dg.JobDefinition)

    # ignore typecheck because we know our implementation doesn't use the context
    assert job.executor_def.executor_creation_fn(None) is executor_inst  # pyright: ignore[reportArgumentType,reportOptionalCall]


def test_assets_with_io_manager():
    @dg.asset
    def single_asset():
        pass

    defs = dg.Definitions(assets=[single_asset], resources={"io_manager": dg.mem_io_manager})

    asset_group_underlying_job = defs.resolve_all_job_defs()[0]
    assert asset_group_underlying_job.resource_defs["io_manager"] == dg.mem_io_manager


def test_asset_missing_resources():
    @dg.asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'asset_foo' was not provided.",
    ):
        Definitions.validate_loadable(dg.Definitions(assets=[asset_foo]))

    source_asset_io_req = dg.SourceAsset(key=dg.AssetKey("foo"), io_manager_key="foo")

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "io manager with key 'foo' required by SourceAsset with key [\"foo\"] was not provided"
        ),
    ):
        Definitions.validate_loadable(dg.Definitions(assets=[source_asset_io_req]))

    external_asset_io_req = create_external_asset_from_source_asset(source_asset_io_req)
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=re.escape(
            "io manager with key 'foo' required by external asset with key [\"foo\"] was not provided"
        ),
    ):
        Definitions.validate_loadable(dg.Definitions(assets=[external_asset_io_req]))


def test_assets_with_executor():
    @dg.asset
    def the_asset():
        pass

    defs = dg.Definitions(assets=[the_asset], executor=in_process_executor)

    asset_group_underlying_job = defs.resolve_all_job_defs()[0]
    assert asset_group_underlying_job.executor_def == dg.in_process_executor


def test_asset_missing_io_manager():
    @dg.asset(io_manager_key="blah")
    def asset_foo():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "io manager with key 'blah' required by output 'result' of op 'asset_foo'' was not"
            " provided."
        ),
    ):
        Definitions.validate_loadable(dg.Definitions(assets=[asset_foo]))


def test_resource_defs_on_asset():
    the_resource = ResourceDefinition.hardcoded_resource("blah")

    @dg.asset(required_resource_keys={"bar"}, resource_defs={"foo": the_resource})
    def the_asset():
        pass

    @dg.asset(resource_defs={"foo": the_resource})
    def other_asset():
        pass

    defs = dg.Definitions([the_asset, other_asset], resources={"bar": the_resource})
    the_job = defs.resolve_all_job_defs()[0]
    assert the_job.execute_in_process().success


def test_conflicting_asset_resource_defs():
    the_resource = ResourceDefinition.hardcoded_resource("blah")
    other_resource = ResourceDefinition.hardcoded_resource("baz")

    @dg.asset(resource_defs={"foo": the_resource})
    def the_asset():
        pass

    @dg.asset(resource_defs={"foo": other_resource})
    def other_asset():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Conflicting versions of resource with key 'foo' were provided to "
            "different assets. When constructing a job, all resource definitions "
            "provided to assets must match by reference equality for a given key."
        ),
    ):
        dg.Definitions([the_asset, other_asset]).resolve_all_job_defs()


def test_graph_backed_asset_resources():
    @dg.op(required_resource_keys={"foo"})
    def the_op():
        pass

    @dg.graph
    def basic():
        return the_op()

    the_resource = ResourceDefinition.hardcoded_resource("blah")
    other_resource = ResourceDefinition.hardcoded_resource("baz")

    the_asset = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("the_asset")},
        resource_defs={"foo": the_resource},
    )
    dg.Definitions([the_asset])

    other_asset = AssetsDefinition.from_graph(
        keys_by_input_name={},
        keys_by_output_name={"result": dg.AssetKey("other_asset")},
        graph_def=basic,
        resource_defs={"foo": other_resource},
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Conflicting versions of resource with key 'foo' were provided to different assets."
            " When constructing a job, all resource definitions provided to assets must match by"
            " reference equality for a given key."
        ),
    ):
        dg.Definitions([the_asset, other_asset]).resolve_all_job_defs()


def test_job_with_reserved_name():
    @dg.graph
    def the_graph():
        pass

    the_job = the_graph.to_job(name="__ASSET_JOB")
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Attempted to provide job called __ASSET_JOB to repository, which is a reserved name."
        ),
    ):
        Definitions.validate_loadable(dg.Definitions(jobs=[the_job]))


def test_asset_cycle():
    @dg.asset
    def a(s, c):
        return s + c

    @dg.asset
    def b(a):
        return a + 1

    @dg.asset
    def c(b):
        return b + 1

    s = dg.SourceAsset(key="s")
    with pytest.raises(CircularDependencyError):
        dg.Definitions(assets=[a, b, c, s]).resolve_all_job_defs()


def test_unsatisfied_resources():
    @dg.asset(required_resource_keys={"foo"})
    def asset1(): ...

    dg.Definitions(assets=[asset1])


def test_unresolved_asset_job():
    @dg.asset(required_resource_keys={"foo"})
    def asset1(): ...

    dg.Definitions(assets=[asset1], jobs=[dg.define_asset_job("job1")])


def test_merge():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    @dg.job
    def job1(): ...

    @dg.job
    def job2(): ...

    schedule1 = dg.ScheduleDefinition(name="schedule1", job=job1, cron_schedule="@daily")
    schedule2 = dg.ScheduleDefinition(name="schedule2", job=job2, cron_schedule="@daily")

    @dg.sensor(job=job1)
    def sensor1(): ...

    @dg.sensor(job=job2)
    def sensor2(): ...

    resource1 = object()
    resource2 = object()

    @dg.logger
    def logger1(_):
        raise Exception("not executed")

    @dg.logger
    def logger2(_):
        raise Exception("not executed")

    mock_module = Mock()
    mock_module.__file__ = Path()
    mock_module.__name__ = "mock_module"
    origin = ComponentTree.from_module(
        defs_module=mock_module,
        project_root=Path(),
    )

    defs1 = dg.Definitions(
        assets=[asset1],
        jobs=[job1],
        schedules=[schedule1],
        sensors=[sensor1],
        resources={"resource1": resource1},
        loggers={"logger1": logger1},
        executor=in_process_executor,
        metadata={"foo": 1},
    )
    defs2 = dg.Definitions(
        assets=[asset2],
        jobs=[job2],
        schedules=[schedule2],
        sensors=[sensor2],
        resources={"resource2": resource2},
        loggers={"logger2": logger2},
        metadata={"bar": 2},
        component_tree=origin,
    )

    merged = Definitions.merge(defs1, defs2)
    assert merged == dg.Definitions(
        assets=[asset1, asset2],
        jobs=[job1, job2],
        schedules=[schedule1, schedule2],
        sensors=[sensor1, sensor2],
        resources={"resource1": resource1, "resource2": resource2},
        loggers={"logger1": logger1, "logger2": logger2},
        executor=in_process_executor,
        asset_checks=[],
        metadata={"foo": MetadataValue.int(1), "bar": MetadataValue.int(2)},
        component_tree=origin,
    )


def test_resource_conflict_on_merge():
    defs1 = dg.Definitions(resources={"resource1": 4})
    defs2 = dg.Definitions(resources={"resource1": 5})

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Definitions objects 0 and 1 have different resources with same key 'resource1'",
    ):
        Definitions.merge(defs1, defs2)


def test_resource_conflict_on_merge_same_value():
    defs1 = dg.Definitions(resources={"resource1": 4})
    defs2 = dg.Definitions(resources={"resource1": 4})

    merged = Definitions.merge(defs1, defs2)
    assert merged.resources == {"resource1": 4}


def test_logger_conflict_on_merge():
    @dg.logger
    def logger1(_):
        raise Exception("not executed")

    @dg.logger
    def logger2(_):
        raise Exception("also not executed")

    defs1 = dg.Definitions(loggers={"logger1": logger1})
    defs2 = dg.Definitions(loggers={"logger1": logger2})

    with pytest.raises(
        dg.DagsterInvariantViolationError,
        match="Definitions objects 0 and 1 have different loggers with same key 'logger1'",
    ):
        Definitions.merge(defs1, defs2)


def test_logger_conflict_on_merge_same_vlaue():
    @dg.logger
    def logger1(_):
        raise Exception("not executed")

    defs1 = dg.Definitions(loggers={"logger1": logger1})
    defs2 = dg.Definitions(loggers={"logger1": logger1})

    merged = Definitions.merge(defs1, defs2)
    assert merged.loggers == {"logger1": logger1}


def test_executor_conflict_on_merge():
    defs1 = dg.Definitions(executor=in_process_executor)
    defs2 = dg.Definitions(executor=multiprocess_executor)

    with pytest.raises(
        dg.DagsterInvariantViolationError, match="Definitions objects 0 and 1 both have an executor"
    ):
        Definitions.merge(defs1, defs2)


def test_merge_resolved_defs():
    defs1 = dg.Definitions(assets=[dg.AssetSpec("asset1")])
    defs2 = dg.Definitions(assets=[dg.AssetSpec("asset2")])

    merged_one = Definitions.merge_unbound_defs(defs1, defs2)

    defs1.resolve_all_asset_specs()

    merged_two = Definitions.merge(defs1, defs2)

    assert merged_one.__dict__ == merged_two.__dict__


def test_merge_unbound_defs_err_resolved():
    defs1 = dg.Definitions(assets=[dg.AssetSpec("asset1")])
    defs2 = dg.Definitions(assets=[dg.AssetSpec("asset2")])

    Definitions.merge_unbound_defs(defs1, defs2)

    defs1.resolve_all_asset_specs()
    with pytest.raises(
        CheckError,
        match="Definitions object 0 has previously been resolved.",
    ):
        Definitions.merge_unbound_defs(defs1, defs2)


def test_executor_conflict_on_merge_same_value():
    defs1 = dg.Definitions(executor=in_process_executor)
    defs2 = dg.Definitions(executor=in_process_executor)

    assert Definitions.merge(defs1, defs2).executor == dg.in_process_executor


def test_spec_remapping_asset_key_collision():
    """Upstream dep asset with same key as real asset should be removed."""
    # Create an upstream dep asset
    marker_asset = dg.AssetSpec(
        "shared_asset",
        metadata={SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET: True},
    )

    # Create an asset that depends on the upstream dep
    dependent_asset = dg.AssetSpec("dependent", deps=["shared_asset"])

    # Create a real asset with the same key
    real_asset = dg.AssetSpec("shared_asset", description="I am the real asset")

    defs = dg.Definitions(assets=[real_asset, marker_asset, dependent_asset])

    all_specs = defs.resolve_all_asset_specs()
    specs_by_key = {spec.key: spec for spec in all_specs}

    # The upstream dep should be removed, only the real asset remains
    assert dg.AssetKey("shared_asset") in specs_by_key
    assert specs_by_key[dg.AssetKey("shared_asset")].description == "I am the real asset"

    # The upstream dep metadata should not be present
    assert (
        SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET
        not in specs_by_key[dg.AssetKey("shared_asset")].metadata
    )

    # The dependent asset should still exist with its dep
    assert dg.AssetKey("dependent") in specs_by_key
    dep_keys = {dep.asset_key for dep in specs_by_key[dg.AssetKey("dependent")].deps}
    assert dg.AssetKey("shared_asset") in dep_keys


def test_spec_remapping_table_name_collision():
    """Upstream dep asset with matching table_name should be removed and deps remapped."""
    # Create an upstream dep asset with table_name
    marker_asset = dg.AssetSpec(
        "placeholder_asset",
        metadata={
            SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET: True,
            **TableMetadataSet(table_name="my_db.my_schema.my_table"),
        },
    )

    # Create an asset that depends on the upstream dep
    dependent_asset = dg.AssetSpec("dependent", deps=["placeholder_asset"])

    # Create a real asset with the same table_name but different key
    real_asset = dg.AssetSpec(
        "actual_table_asset",
        metadata={**TableMetadataSet(table_name="my_db.my_schema.my_table")},
    )

    defs = dg.Definitions(assets=[real_asset, marker_asset, dependent_asset])
    all_specs = defs.resolve_all_asset_specs()
    specs_by_key = {spec.key: spec for spec in all_specs}

    # The upstream dep should be removed
    assert dg.AssetKey("placeholder_asset") not in specs_by_key

    # The real asset should exist
    assert dg.AssetKey("actual_table_asset") in specs_by_key

    # The dependent asset should have its dep remapped to the real asset
    assert dg.AssetKey("dependent") in specs_by_key
    dep_keys = {dep.asset_key for dep in specs_by_key[dg.AssetKey("dependent")].deps}
    assert dg.AssetKey("actual_table_asset") in dep_keys
    assert dg.AssetKey("placeholder_asset") not in dep_keys


def test_spec_remapping_no_collision():
    """Upstream dep asset with no match should be preserved."""
    # Create an upstream dep asset with no matching real asset
    marker_asset = dg.AssetSpec(
        "external_dep",
        metadata={SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET: True},
    )

    # Create an asset that depends on the upstream dep
    dependent_asset = dg.AssetSpec("dependent", deps=["external_dep"])

    # Create another unrelated asset
    other_asset = dg.AssetSpec("other_asset")

    defs = dg.Definitions(assets=[marker_asset, dependent_asset, other_asset])
    all_specs = defs.resolve_all_asset_specs()
    specs_by_key = {spec.key: spec for spec in all_specs}

    # The upstream dep should be preserved since there's no match
    assert dg.AssetKey("external_dep") in specs_by_key

    # The dependent asset should still reference the upstream dep
    assert dg.AssetKey("dependent") in specs_by_key
    dep_keys = {dep.asset_key for dep in specs_by_key[dg.AssetKey("dependent")].deps}
    assert dg.AssetKey("external_dep") in dep_keys


def test_spec_remapping_multiple_collisions():
    """Multiple assets with same table_name should raise an error if there's a marker asset that matches the table_name."""
    # Create an upstream dep asset with table_name
    marker_asset = dg.AssetSpec(
        "placeholder",
        metadata={
            SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET: True,
            **TableMetadataSet(table_name="shared_table"),
        },
    )

    dependent_asset = dg.AssetSpec("dependent", deps=["placeholder"])

    # Create two assets with the same table_name - first one should win
    first_asset = dg.AssetSpec(
        "first_asset",
        metadata={**TableMetadataSet(table_name="shared_table")},
    )
    second_asset = dg.AssetSpec(
        "second_asset",
        metadata={**TableMetadataSet(table_name="shared_table")},
    )

    # ok to share table name without a marker asset
    defs_ok = dg.Definitions(assets=[first_asset, second_asset, dependent_asset])
    assert len(defs_ok.resolve_all_asset_specs()) == 4  # 1 extra for stub asset

    defs_err = dg.Definitions.merge(defs_ok, dg.Definitions(assets=[marker_asset]))
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="shared_table",
    ):
        defs_err.resolve_all_asset_specs()


def test_spec_remapping_with_assets_definition():
    """Test that upstream dep reconciliation works with AssetsDefinition objects."""
    # Create an upstream dep asset
    upstream_dep = dg.AssetSpec(
        "placeholder",
        metadata={
            SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET: True,
            **TableMetadataSet(table_name="shared_table"),
        },
    )

    # Create an @asset decorated function that depends on the upstream dep
    @dg.asset(deps=["placeholder"])
    def downstream_asset():
        pass

    # Create a real asset with the same key
    real_source = dg.AssetSpec(
        "actual_table_asset",
        description="Real source",
        metadata={**TableMetadataSet(table_name="shared_table")},
    )

    defs = dg.Definitions(assets=[real_source, upstream_dep, downstream_asset])
    all_specs = defs.resolve_all_asset_specs()
    specs_by_key = {spec.key: spec for spec in all_specs}

    node = defs.resolve_asset_graph().get(dg.AssetKey("downstream_asset"))
    assert node.parent_keys == {dg.AssetKey("actual_table_asset")}

    # The real asset should be present, not the upstream dep
    assert dg.AssetKey("actual_table_asset") in specs_by_key
    assert specs_by_key[dg.AssetKey("actual_table_asset")].description == "Real source"

    assert dg.AssetKey("placeholder") not in specs_by_key


def test_spec_remapping_with_asset_check_definition():
    """Test that upstream dep reconciliation works with AssetsDefinition objects."""
    # Create an upstream dep asset
    marker_asset = dg.AssetSpec(
        "placeholder",
        metadata={
            SYSTEM_METADATA_KEY_UPSTREAM_DEP_MARKER_ASSET: True,
            **TableMetadataSet(table_name="shared_table"),
        },
    )

    # Create an @asset decorated function that depends on the upstream dep
    @dg.asset_check(asset=dg.AssetKey("placeholder"))
    def downstream_check() -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    # Create a real asset with the same key
    real_source = dg.AssetSpec(
        "external_source",
        description="Real source",
        metadata={**TableMetadataSet(table_name="shared_table")},
    )

    defs = dg.Definitions(assets=[real_source, marker_asset], asset_checks=[downstream_check])
    all_specs = defs.resolve_all_asset_specs()
    specs_by_key = {spec.key: spec for spec in all_specs}

    # The real asset should be present, not the upstream dep
    assert dg.AssetKey("external_source") in specs_by_key
    assert specs_by_key[dg.AssetKey("external_source")].description == "Real source"

    # check key should have been updated
    node = defs.resolve_asset_graph().get(
        dg.AssetCheckKey(dg.AssetKey("external_source"), "downstream_check")
    )
    assert node.parent_entity_keys == {dg.AssetKey("external_source")}


def test_get_all_asset_specs():
    @dg.asset(tags={"foo": "fooval"})
    def asset1(): ...

    @dg.asset
    def asset2(asset1): ...

    @dg.multi_asset(specs=[dg.AssetSpec("asset3"), dg.AssetSpec("asset4", group_name="baz")])
    def assets3_and_4(): ...

    asset5 = dg.SourceAsset("asset5", tags={"biz": "boz"})

    @dg.observable_source_asset(group_name="blag")
    def asset6(): ...

    asset7 = dg.AssetSpec("asset7", tags={"apple": "banana"})

    defs = dg.Definitions(assets=[asset1, asset2, assets3_and_4, asset5, asset6, asset7])
    all_asset_specs = defs.resolve_all_asset_specs()
    assert len(all_asset_specs) == 7
    asset_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert asset_specs_by_key.keys() == {
        dg.AssetKey(s)
        for s in ["asset1", "asset2", "asset3", "asset4", "asset5", "asset6", "asset7"]
    }
    assert asset_specs_by_key[dg.AssetKey("asset1")] == dg.AssetSpec(
        "asset1", tags={"foo": "fooval"}, group_name="default"
    )
    assert asset_specs_by_key[dg.AssetKey("asset2")] == dg.AssetSpec(
        "asset2", group_name="default", deps=[dg.AssetDep("asset1")]
    )
    assert asset_specs_by_key[dg.AssetKey("asset3")] == dg.AssetSpec("asset3", group_name="default")
    assert asset_specs_by_key[dg.AssetKey("asset4")] == dg.AssetSpec("asset4", group_name="baz")
    assert asset_specs_by_key[dg.AssetKey("asset5")] == dg.AssetSpec(
        "asset5",
        group_name="default",
        tags={"biz": "boz"},
    )
    assert asset_specs_by_key[dg.AssetKey("asset6")] == dg.AssetSpec("asset6", group_name="blag")
    assert asset_specs_by_key[dg.AssetKey("asset7")] == asset7._replace(group_name="default")


def test_asset_specs_different_partitions():
    asset1 = dg.AssetSpec("asset1", partitions_def=dg.StaticPartitionsDefinition(["a", "b"]))
    asset2 = dg.AssetSpec("asset2", partitions_def=dg.StaticPartitionsDefinition(["1", "2"]))
    Definitions.validate_loadable(dg.Definitions(assets=[asset1, asset2]))


def test_asset_spec_dependencies_in_graph() -> None:
    upstream_asset = dg.AssetSpec("upstream_asset")
    downstream_asset = dg.AssetSpec("downstream_asset", deps=[upstream_asset])

    defs = dg.Definitions(assets=[upstream_asset, downstream_asset])

    assert defs.resolve_asset_graph().asset_dep_graph["upstream"][downstream_asset.key] == {
        upstream_asset.key
    }


def test_invalid_partitions_subclass():
    class CustomPartitionsDefinition(dg.PartitionsDefinition):
        def get_partition_keys(
            self,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Any = None,
        ) -> Sequence[str]:
            return ["a", "b", "c"]

        def get_paginated_partition_keys(
            self,
            context: PartitionLoadingContext,
            limit: int,
            ascending: bool,
            cursor: Optional[str] = None,
        ) -> dg.PaginatedResults[str]:
            partition_keys = self.get_partition_keys(
                current_time=context.temporal_context.effective_dt,
                dynamic_partitions_store=context.dynamic_partitions_store,
            )
            return PaginatedResults.create_from_sequence(
                partition_keys, limit=limit, ascending=ascending, cursor=cursor
            )

    @dg.asset(partitions_def=CustomPartitionsDefinition())
    def asset1():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Custom PartitionsDefinition subclasses",
    ):
        Definitions.validate_loadable(dg.Definitions(assets=[asset1]))


def test_hoist_automation_assets():
    @dg.asset
    def foo():
        pass

    @dg.asset
    def bar():
        pass

    @dg.sensor(name="foo_sensor", target=foo)
    def foo_sensor():
        pass

    @dg.schedule(name="bar_schedule", cron_schedule="* * * * *", target=bar)
    def bar_schedule():
        pass

    foo_job = dg.define_asset_job("foo_job", selection=[foo])

    defs = dg.Definitions(sensors=[foo_sensor], schedules=[bar_schedule], jobs=[foo_job])

    assert defs.resolve_assets_def(foo.key) == foo
    assert defs.resolve_assets_def(bar.key) == bar

    # We can define and execute asset jobs that reference assets only defined in targets
    assert defs.resolve_job_def(foo_job.name).execute_in_process().success


def test_definitions_failure_on_asset_job_resolve():
    @dg.asset
    def asset_not_in_defs():
        pass

    invalid_job = dg.define_asset_job("invalid_job", selection=[asset_not_in_defs])

    defs = dg.Definitions(
        jobs=[invalid_job],
    )

    with pytest.raises(dg.DagsterInvalidDefinitionError) as exc_info:
        Definitions.validate_loadable(defs)

    tb_exc = traceback.TracebackException.from_exception(exc_info.value)
    error_info = SerializableErrorInfo.from_traceback(tb_exc)
    assert "no AssetsDefinition objects supply these keys" in str(error_info)


def test_definitions_dedupe_reference_equality():
    """Test that Definitions objects correctly dedupe objects by
    reference equality.
    """

    @dg.asset
    def the_asset():
        pass

    @dg.asset_check(asset=the_asset)
    def the_check():
        return dg.AssetCheckResult(passed=True)

    the_job = dg.define_asset_job(name="the_job", selection="the_asset")

    @dg.sensor(job=the_job)
    def the_sensor():
        pass

    @dg.schedule(job=the_job, cron_schedule="* * * * *")
    def the_schedule():
        pass

    defs = dg.Definitions(
        assets=[the_asset, the_asset],
        asset_checks=[the_check, the_check],
        jobs=[the_job, the_job],
        sensors=[the_sensor, the_sensor],
        schedules=[the_schedule, the_schedule],
    )
    underlying_repo = defs.get_repository_def()
    assert (
        len(
            [
                assets_def
                for assets_def in underlying_repo.asset_graph.assets_defs
                if not isinstance(assets_def, dg.AssetChecksDefinition)
            ]
        )
        == 1
    )
    assert len(list(underlying_repo.asset_graph._assets_defs_by_check_key)) == 1  # noqa
    assert (
        len(
            [job_def for job_def in underlying_repo.get_all_jobs() if job_def.name != "__ASSET_JOB"]
        )
        == 1
    )
    assert len(list(underlying_repo.sensor_defs)) == 1
    assert len(list(underlying_repo.schedule_defs)) == 1

    # properties on the definitions object do not dedupe
    assert len(defs.assets) == 2  # pyright: ignore[reportArgumentType]
    assert len(defs.asset_checks) == 2  # pyright: ignore[reportArgumentType]
    assert len(defs.jobs) == 2  # pyright: ignore[reportArgumentType]
    assert len(defs.sensors) == 2  # pyright: ignore[reportArgumentType]
    assert len(defs.schedules) == 2  # pyright: ignore[reportArgumentType]


def test_definitions_class_metadata():
    defs = dg.Definitions(metadata={"foo": "bar"})
    assert defs.metadata == {"foo": MetadataValue.text("bar")}
    assert defs.get_repository_def().metadata == {"foo": MetadataValue.text("bar")}


def test_assets_def_with_only_checks():
    @dg.asset_check(asset="asset1")  # pyright: ignore[reportArgumentType]
    def check1():
        pass

    assets_def = dg.AssetsDefinition(**check1.get_attributes_dict())
    defs = dg.Definitions(assets=[assets_def])
    check_key = dg.AssetCheckKey(dg.AssetKey("asset1"), "check1")
    assert defs.resolve_asset_graph().asset_check_keys == {check_key}
    assert check_key in defs.get_repository_def().asset_checks_defs_by_key


def test_map_asset_specs() -> None:
    specs = [dg.AssetSpec("asset1"), dg.AssetSpec("asset2")]
    defs = dg.Definitions(assets=specs)
    spec_lambda = lambda spec: spec.merge_attributes(tags={"foo": "bar"})
    mapped_defs = defs.map_resolved_asset_specs(func=spec_lambda)
    assert mapped_defs.assets == [
        dg.AssetSpec("asset1", tags={"foo": "bar"}),
        dg.AssetSpec("asset2", tags={"foo": "bar"}),
    ]

    # Select only asset 1
    mapped_defs = defs.map_resolved_asset_specs(func=spec_lambda, selection="asset1")
    assert mapped_defs.assets == [
        dg.AssetSpec("asset1", tags={"foo": "bar"}),
        dg.AssetSpec("asset2"),
    ]

    # Select no assets accidentally
    with pytest.raises(dg.DagsterInvalidSubsetError):
        mapped_defs = defs.map_resolved_asset_specs(func=spec_lambda, selection="asset3")

    # attempt to map with source asset
    source_asset = dg.SourceAsset("source_asset")
    defs = dg.Definitions(assets=[source_asset])
    with pytest.raises(dg.DagsterInvariantViolationError):
        defs.map_resolved_asset_specs(func=spec_lambda)

    class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return []

        def build_definitions(self, data):
            return []

    cacheable_asset = MyCacheableAssetsDefinition("cacheable_asset")
    defs = dg.Definitions(assets=[cacheable_asset])
    with pytest.raises(dg.DagsterInvariantViolationError):
        defs.map_resolved_asset_specs(func=spec_lambda)
