import re
from datetime import datetime
from typing import Any, Optional, Sequence

import pytest
from dagster import (
    AssetDep,
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    DagsterInvalidDefinitionError,
    Definitions,
    ResourceDefinition,
    ScheduleDefinition,
    SourceAsset,
    asset,
    asset_check,
    build_schedule_from_partitioned_job,
    create_repository_using_definitions_args,
    define_asset_job,
    graph,
    in_process_executor,
    materialize,
    mem_io_manager,
    multi_asset,
    multiprocess_executor,
    observable_source_asset,
    op,
    schedule,
    sensor,
    with_resources,
)
from dagster._check import CheckError
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.decorators.job_decorator import job
from dagster._core.definitions.executor_definition import executor
from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import logger
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.partition import PartitionsDefinition, StaticPartitionsDefinition
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster._core.errors import DagsterInvalidSubsetError, DagsterInvariantViolationError
from dagster._core.executor.base import Executor
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._core.storage.mem_io_manager import InMemoryIOManager
from dagster._core.test_utils import instance_for_test
from dagster._utils.test.definitions import scoped_definitions_load_context


def get_all_assets_from_defs(defs: Definitions):
    return list(defs.get_repository_def().asset_graph.assets_defs)


def test_basic_asset():
    assert Definitions

    @asset
    def an_asset():
        pass

    defs = Definitions(assets=[an_asset])

    all_assets = get_all_assets_from_defs(defs)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "an_asset"


def test_basic_asset_job_definition():
    @asset
    def an_asset():
        pass

    defs = Definitions(assets=[an_asset], jobs=[define_asset_job(name="an_asset_job")])

    assert isinstance(defs.get_job_def("an_asset_job"), JobDefinition)


def test_vanilla_job_definition():
    @op
    def an_op():
        pass

    @job
    def a_job():
        pass

    defs = Definitions(jobs=[a_job])
    assert isinstance(defs.get_job_def("a_job"), JobDefinition)


def test_basic_schedule_definition():
    @asset
    def an_asset():
        pass

    defs = Definitions(
        assets=[an_asset],
        schedules=[
            ScheduleDefinition(
                name="daily_an_asset_schedule",
                job=define_asset_job(name="an_asset_job"),
                cron_schedule="@daily",
            )
        ],
    )

    assert defs.get_schedule_def("daily_an_asset_schedule")


def test_basic_sensor_definition():
    @asset
    def an_asset():
        pass

    an_asset_job = define_asset_job(name="an_asset_job")

    @sensor(name="an_asset_sensor", job=an_asset_job)
    def a_sensor():
        raise NotImplementedError()

    defs = Definitions(
        assets=[an_asset],
        sensors=[a_sensor],
    )

    assert defs.get_sensor_def("an_asset_sensor")


def test_with_resource_binding():
    executed = {}

    @asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "wrapped"
        executed["yes"] = True

    defs = Definitions(
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
    class MyInnerResource(ConfigurableResource):
        a_str: str

    class MyOuterResource(ConfigurableResource):
        inner: MyInnerResource

    inner = MyInnerResource(a_str="wrapped")
    defs = Definitions(
        resources={"foo": MyOuterResource(inner=inner)},
    )
    repo = defs.get_repository_def()

    assert len(repo.get_top_level_resources()) == 1
    assert "foo" in repo.get_top_level_resources()


def test_resource_coercion():
    executed = {}

    @asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "object-to-coerce"
        executed["yes"] = True

    defs = Definitions(
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
    defs = Definitions(assets=[SourceAsset("a-source-asset")])
    repo = defs.get_repository_def()
    all_assets = list(repo.asset_graph.assets_defs)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "a-source-asset"


def test_cacheable_asset_repo():
    class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={}, keys_by_output_name={"result": AssetKey(self.unique_id)}
                )
            ]

        def build_definitions(self, data):
            @op
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
        defs = Definitions(assets=[MyCacheableAssetsDefinition("foobar")])
        all_assets = get_all_assets_from_defs(defs)
        assert len(all_assets) == 1
        assert all_assets[0].key.to_user_string() == "foobar"

        assert isinstance(defs.get_implicit_global_asset_job_def(), JobDefinition)


def test_asset_loading():
    @asset
    def one():
        return 1

    @asset
    def two():
        return 2

    with instance_for_test() as instance:
        defs = Definitions(assets=[one, two])
        materialize(assets=[one, two], instance=instance)
        assert defs.load_asset_value("one", instance=instance) == 1
        assert defs.load_asset_value("two", instance=instance) == 2

        value_loader = defs.get_asset_value_loader(instance)
        assert value_loader.load_asset_value("one") == 1
        assert value_loader.load_asset_value("two") == 2


def test_io_manager_coercion():
    @asset(io_manager_key="mem_io_manager")
    def one():
        return 1

    defs = Definitions(assets=[one], resources={"mem_io_manager": InMemoryIOManager()})

    asset_job = defs.get_implicit_global_asset_job_def()
    assert isinstance(asset_job.resource_defs["mem_io_manager"], IOManagerDefinition)
    result = asset_job.execute_in_process()
    assert result.output_for_node("one") == 1


def test_bad_executor():
    with pytest.raises(CheckError):
        # ignoring type to catch runtime error
        Definitions(executor="not an executor")


def test_custom_executor_in_definitions():
    @executor
    def an_executor(_):
        raise Exception("not executed")

    @asset
    def one():
        return 1

    defs = Definitions(assets=[one], executor=an_executor)
    asset_job = defs.get_implicit_global_asset_job_def()
    assert asset_job.executor_def is an_executor


def test_custom_loggers_in_definitions():
    @logger
    def a_logger(_):
        raise Exception("not executed")

    @asset
    def one():
        return 1

    defs = Definitions(assets=[one], loggers={"custom_logger": a_logger})

    asset_job = defs.get_implicit_global_asset_job_def()
    loggers = asset_job.loggers
    assert len(loggers) == 1
    assert "custom_logger" in loggers
    assert loggers["custom_logger"] is a_logger


def test_bad_logger_key():
    @logger
    def a_logger(_):
        raise Exception("not executed")

    with pytest.raises(CheckError):
        # ignore type to catch runtime error
        Definitions(loggers={1: a_logger})


def test_bad_logger_value():
    with pytest.raises(CheckError):
        # ignore type to catch runtime error
        Definitions(loggers={"not_a_logger": "not_a_logger"})


def test_kitchen_sink_on_create_helper_and_definitions():
    @asset(required_resource_keys={"a_resource_key"})
    def an_asset():
        pass

    @asset
    def another_asset():
        pass

    another_asset_job = define_asset_job(name="another_asset_job", selection="another_asset")

    @op
    def an_op():
        pass

    @job
    def a_job():
        an_op()

    @job
    def sensor_target():
        an_op()

    @job
    def schedule_target():
        an_op()

    a_schedule = ScheduleDefinition(name="a_schedule", job=schedule_target, cron_schedule="@daily")

    @sensor(job=sensor_target)
    def a_sensor(_):
        raise Exception("not called")

    @executor
    def an_executor(_):
        raise Exception("not executed")

    @logger
    def a_logger(_):
        raise Exception("not executed")

    repo = create_repository_using_definitions_args(
        name="foobar",
        assets=[an_asset, another_asset],
        jobs=[a_job, another_asset_job],
        schedules=[a_schedule],
        sensors=[a_sensor],
        resources={"a_resource_key": "the resource"},
        executor=an_executor,
        loggers={"logger_key": a_logger},
    )

    assert isinstance(repo, RepositoryDefinition)

    assert repo.name == "foobar"
    assert isinstance(repo.get_job("a_job"), JobDefinition)
    assert repo.get_job("a_job").executor_def is an_executor
    assert repo.get_job("a_job").loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_implicit_global_asset_job_def(), JobDefinition)
    assert repo.get_implicit_global_asset_job_def().executor_def is an_executor
    assert repo.get_implicit_global_asset_job_def().loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_job("another_asset_job"), JobDefinition)
    assert repo.get_job("another_asset_job").executor_def is an_executor
    assert repo.get_job("another_asset_job").loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_job("sensor_target"), JobDefinition)
    assert repo.get_job("sensor_target").executor_def is an_executor
    assert repo.get_job("sensor_target").loggers == {"logger_key": a_logger}
    assert isinstance(repo.get_job("schedule_target"), JobDefinition)
    assert repo.get_job("schedule_target").executor_def is an_executor
    assert repo.get_job("schedule_target").loggers == {"logger_key": a_logger}

    assert isinstance(repo.get_schedule_def("a_schedule"), ScheduleDefinition)
    assert isinstance(repo.get_sensor_def("a_sensor"), SensorDefinition)

    # test the kitchen sink since we have created it
    defs = Definitions(
        assets=[an_asset, another_asset],
        jobs=[a_job, another_asset_job],
        schedules=[a_schedule],
        sensors=[a_sensor],
        resources={"a_resource_key": "the resource"},
        executor=an_executor,
        loggers={"logger_key": a_logger},
    )

    assert isinstance(defs.get_job_def("a_job"), JobDefinition)
    assert defs.get_job_def("a_job").executor_def is an_executor
    assert defs.get_job_def("a_job").loggers == {"logger_key": a_logger}
    assert isinstance(defs.get_implicit_global_asset_job_def(), JobDefinition)
    assert defs.get_implicit_global_asset_job_def().executor_def is an_executor
    assert defs.get_implicit_global_asset_job_def().loggers == {"logger_key": a_logger}
    assert isinstance(defs.get_job_def("another_asset_job"), JobDefinition)
    assert defs.get_job_def("another_asset_job").executor_def is an_executor
    assert defs.get_job_def("another_asset_job").loggers == {"logger_key": a_logger}
    assert isinstance(defs.get_job_def("sensor_target"), JobDefinition)
    assert defs.get_job_def("sensor_target").executor_def is an_executor
    assert defs.get_job_def("sensor_target").loggers == {"logger_key": a_logger}
    assert isinstance(defs.get_job_def("schedule_target"), JobDefinition)
    assert defs.get_job_def("schedule_target").executor_def is an_executor
    assert defs.get_job_def("schedule_target").loggers == {"logger_key": a_logger}

    assert isinstance(defs.get_schedule_def("a_schedule"), ScheduleDefinition)
    assert isinstance(defs.get_sensor_def("a_sensor"), SensorDefinition)


def test_with_resources_override():
    executed = {}

    @asset(required_resource_keys={"a_resource"})
    def asset_one(context):
        executed["asset_one"] = True
        assert context.resources.a_resource == "passed-through-with-resources"

    @asset(required_resource_keys={"b_resource"})
    def asset_two(context):
        executed["asset_two"] = True
        assert context.resources.b_resource == "passed-through-definitions"

    defs = Definitions(
        assets=[
            *with_resources(
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

    defs.get_implicit_global_asset_job_def().execute_in_process()

    assert executed["asset_one"]
    assert executed["asset_two"]


def test_implicit_global_job():
    @asset
    def asset_one():
        pass

    defs = Definitions(assets=[asset_one])

    assert defs.has_implicit_global_asset_job_def()
    assert len(defs.get_all_job_defs()) == 1


def test_implicit_global_job_with_job_defined():
    @asset
    def asset_one():
        pass

    defs = Definitions(assets=[asset_one], jobs=[define_asset_job("all_assets_job", selection="*")])

    assert defs.has_implicit_global_asset_job_def()
    assert defs.get_job_def("all_assets_job")
    assert defs.get_job_def("all_assets_job") is not defs.get_implicit_global_asset_job_def()

    assert len(defs.get_all_job_defs()) == 2


def test_implicit_global_job_with_partitioned_asset():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def daily_partition_asset(context: AssetExecutionContext):
        return context.partition_key

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-02-02-10:00"))
    def hourly_partition_asset(context: AssetExecutionContext):
        return context.partition_key

    @asset
    def unpartitioned_asset():
        pass

    defs = Definitions(
        assets=[daily_partition_asset, unpartitioned_asset, hourly_partition_asset],
    )

    assert len(defs.get_all_job_defs()) == 1
    defs.get_implicit_global_asset_job_def()


def test_implicit_job_with_source_assets():
    source_asset = SourceAsset("source_asset")

    @asset
    def downstream_of_source(source_asset):
        raise Exception("not executed")

    defs = Definitions(assets=[source_asset, downstream_of_source])
    assert defs.get_all_job_defs()
    assert len(defs.get_all_job_defs()) == 1
    assert defs.get_implicit_job_def_for_assets(asset_keys=[AssetKey("downstream_of_source")])
    assert defs.has_implicit_global_asset_job_def()
    assert defs.get_implicit_global_asset_job_def()


def test_unresolved_partitioned_asset_schedule():
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(partitions_def=partitions_def)
    def asset1(): ...

    job1 = define_asset_job("job1")
    schedule1 = build_schedule_from_partitioned_job(job1)

    defs_with_explicit_job = Definitions(jobs=[job1], schedules=[schedule1], assets=[asset1])
    assert defs_with_explicit_job.get_job_def("job1").name == "job1"
    assert defs_with_explicit_job.get_job_def("job1").partitions_def == partitions_def
    assert defs_with_explicit_job.get_schedule_def("job1_schedule").cron_schedule == "0 0 * * *"

    defs_with_implicit_job = Definitions(schedules=[schedule1], assets=[asset1])
    assert defs_with_implicit_job.get_job_def("job1").name == "job1"
    assert defs_with_implicit_job.get_job_def("job1").partitions_def == partitions_def
    assert defs_with_implicit_job.get_schedule_def("job1_schedule").cron_schedule == "0 0 * * *"


def test_bare_executor():
    @asset
    def an_asset(): ...

    class DummyExecutor(Executor):
        def execute(self, plan_context, execution_plan): ...

        @property
        def retries(self): ...

    executor_inst = DummyExecutor()

    defs = Definitions(assets=[an_asset], executor=executor_inst)

    job = defs.get_implicit_global_asset_job_def()
    assert isinstance(job, JobDefinition)

    # ignore typecheck because we know our implementation doesn't use the context
    assert job.executor_def.executor_creation_fn(None) is executor_inst


def test_assets_with_io_manager():
    @asset
    def single_asset():
        pass

    defs = Definitions(assets=[single_asset], resources={"io_manager": mem_io_manager})

    asset_group_underlying_job = defs.get_all_job_defs()[0]
    assert asset_group_underlying_job.resource_defs["io_manager"] == mem_io_manager


def test_asset_missing_resources():
    @asset(required_resource_keys={"foo"})
    def asset_foo(context):
        return context.resources.foo

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'foo' required by op 'asset_foo' was not provided.",
    ):
        Definitions.validate_loadable(Definitions(assets=[asset_foo]))

    source_asset_io_req = SourceAsset(key=AssetKey("foo"), io_manager_key="foo")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "io manager with key 'foo' required by SourceAsset with key [\"foo\"] was not provided"
        ),
    ):
        Definitions.validate_loadable(Definitions(assets=[source_asset_io_req]))

    external_asset_io_req = create_external_asset_from_source_asset(source_asset_io_req)
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "io manager with key 'foo' required by external asset with key [\"foo\"] was not provided"
        ),
    ):
        Definitions.validate_loadable(Definitions(assets=[external_asset_io_req]))


def test_assets_with_executor():
    @asset
    def the_asset():
        pass

    defs = Definitions(assets=[the_asset], executor=in_process_executor)

    asset_group_underlying_job = defs.get_all_job_defs()[0]
    assert asset_group_underlying_job.executor_def == in_process_executor


def test_asset_missing_io_manager():
    @asset(io_manager_key="blah")
    def asset_foo():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "io manager with key 'blah' required by output 'result' of op 'asset_foo'' was not"
            " provided."
        ),
    ):
        Definitions.validate_loadable(Definitions(assets=[asset_foo]))


def test_resource_defs_on_asset():
    the_resource = ResourceDefinition.hardcoded_resource("blah")

    @asset(required_resource_keys={"bar"}, resource_defs={"foo": the_resource})
    def the_asset():
        pass

    @asset(resource_defs={"foo": the_resource})
    def other_asset():
        pass

    defs = Definitions([the_asset, other_asset], resources={"bar": the_resource})
    the_job = defs.get_all_job_defs()[0]
    assert the_job.execute_in_process().success


def test_conflicting_asset_resource_defs():
    the_resource = ResourceDefinition.hardcoded_resource("blah")
    other_resource = ResourceDefinition.hardcoded_resource("baz")

    @asset(resource_defs={"foo": the_resource})
    def the_asset():
        pass

    @asset(resource_defs={"foo": other_resource})
    def other_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Conflicting versions of resource with key 'foo' were provided to "
            "different assets. When constructing a job, all resource definitions "
            "provided to assets must match by reference equality for a given key."
        ),
    ):
        Definitions([the_asset, other_asset]).get_all_job_defs()


def test_graph_backed_asset_resources():
    @op(required_resource_keys={"foo"})
    def the_op():
        pass

    @graph
    def basic():
        return the_op()

    the_resource = ResourceDefinition.hardcoded_resource("blah")
    other_resource = ResourceDefinition.hardcoded_resource("baz")

    the_asset = AssetsDefinition.from_graph(
        graph_def=basic,
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey("the_asset")},
        resource_defs={"foo": the_resource},
    )
    Definitions([the_asset])

    other_asset = AssetsDefinition.from_graph(
        keys_by_input_name={},
        keys_by_output_name={"result": AssetKey("other_asset")},
        graph_def=basic,
        resource_defs={"foo": other_resource},
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Conflicting versions of resource with key 'foo' were provided to different assets."
            " When constructing a job, all resource definitions provided to assets must match by"
            " reference equality for a given key."
        ),
    ):
        Definitions([the_asset, other_asset]).get_all_job_defs()


def test_job_with_reserved_name():
    @graph
    def the_graph():
        pass

    the_job = the_graph.to_job(name="__ASSET_JOB")
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Attempted to provide job called __ASSET_JOB to repository, which is a reserved name."
        ),
    ):
        Definitions.validate_loadable(Definitions(jobs=[the_job]))


def test_asset_cycle():
    from toposort import CircularDependencyError

    @asset
    def a(s, c):
        return s + c

    @asset
    def b(a):
        return a + 1

    @asset
    def c(b):
        return b + 1

    s = SourceAsset(key="s")
    with pytest.raises(CircularDependencyError):
        Definitions(assets=[a, b, c, s]).get_all_job_defs()


def test_unsatisfied_resources():
    @asset(required_resource_keys={"foo"})
    def asset1(): ...

    Definitions(assets=[asset1])


def test_unresolved_asset_job():
    @asset(required_resource_keys={"foo"})
    def asset1(): ...

    Definitions(assets=[asset1], jobs=[define_asset_job("job1")])


def test_merge():
    @asset
    def asset1(): ...

    @asset
    def asset2(): ...

    @job
    def job1(): ...

    @job
    def job2(): ...

    schedule1 = ScheduleDefinition(name="schedule1", job=job1, cron_schedule="@daily")
    schedule2 = ScheduleDefinition(name="schedule2", job=job2, cron_schedule="@daily")

    @sensor(job=job1)
    def sensor1(): ...

    @sensor(job=job2)
    def sensor2(): ...

    resource1 = object()
    resource2 = object()

    @logger
    def logger1(_):
        raise Exception("not executed")

    @logger
    def logger2(_):
        raise Exception("not executed")

    defs1 = Definitions(
        assets=[asset1],
        jobs=[job1],
        schedules=[schedule1],
        sensors=[sensor1],
        resources={"resource1": resource1},
        loggers={"logger1": logger1},
        executor=in_process_executor,
        metadata={"foo": 1},
    )
    defs2 = Definitions(
        assets=[asset2],
        jobs=[job2],
        schedules=[schedule2],
        sensors=[sensor2],
        resources={"resource2": resource2},
        loggers={"logger2": logger2},
        metadata={"bar": 2},
    )

    merged = Definitions.merge(defs1, defs2)
    assert merged == Definitions(
        assets=[asset1, asset2],
        jobs=[job1, job2],
        schedules=[schedule1, schedule2],
        sensors=[sensor1, sensor2],
        resources={"resource1": resource1, "resource2": resource2},
        loggers={"logger1": logger1, "logger2": logger2},
        executor=in_process_executor,
        asset_checks=[],
        metadata={"foo": MetadataValue.int(1), "bar": MetadataValue.int(2)},
    )


def test_resource_conflict_on_merge():
    defs1 = Definitions(resources={"resource1": 4})
    defs2 = Definitions(resources={"resource1": 5})

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Definitions objects 0 and 1 have different resources with same key 'resource1'",
    ):
        Definitions.merge(defs1, defs2)


def test_resource_conflict_on_merge_same_value():
    defs1 = Definitions(resources={"resource1": 4})
    defs2 = Definitions(resources={"resource1": 4})

    merged = Definitions.merge(defs1, defs2)
    assert merged.resources == {"resource1": 4}


def test_logger_conflict_on_merge():
    @logger
    def logger1(_):
        raise Exception("not executed")

    @logger
    def logger2(_):
        raise Exception("also not executed")

    defs1 = Definitions(loggers={"logger1": logger1})
    defs2 = Definitions(loggers={"logger1": logger2})

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Definitions objects 0 and 1 have different loggers with same key 'logger1'",
    ):
        Definitions.merge(defs1, defs2)


def test_logger_conflict_on_merge_same_vlaue():
    @logger
    def logger1(_):
        raise Exception("not executed")

    defs1 = Definitions(loggers={"logger1": logger1})
    defs2 = Definitions(loggers={"logger1": logger1})

    merged = Definitions.merge(defs1, defs2)
    assert merged.loggers == {"logger1": logger1}


def test_executor_conflict_on_merge():
    defs1 = Definitions(executor=in_process_executor)
    defs2 = Definitions(executor=multiprocess_executor)

    with pytest.raises(
        DagsterInvariantViolationError, match="Definitions objects 0 and 1 both have an executor"
    ):
        Definitions.merge(defs1, defs2)


def test_executor_conflict_on_merge_same_value():
    defs1 = Definitions(executor=in_process_executor)
    defs2 = Definitions(executor=in_process_executor)

    assert Definitions.merge(defs1, defs2).executor == in_process_executor


def test_get_all_asset_specs():
    @asset(tags={"foo": "fooval"})
    def asset1(): ...

    @asset
    def asset2(asset1): ...

    @multi_asset(specs=[AssetSpec("asset3"), AssetSpec("asset4", group_name="baz")])
    def assets3_and_4(): ...

    asset5 = SourceAsset("asset5", tags={"biz": "boz"})

    @observable_source_asset(group_name="blag")
    def asset6(): ...

    asset7 = AssetSpec("asset7", tags={"apple": "banana"})

    defs = Definitions(assets=[asset1, asset2, assets3_and_4, asset5, asset6, asset7])
    all_asset_specs = defs.get_all_asset_specs()
    assert len(all_asset_specs) == 7
    asset_specs_by_key = {spec.key: spec for spec in all_asset_specs}
    assert asset_specs_by_key.keys() == {
        AssetKey(s) for s in ["asset1", "asset2", "asset3", "asset4", "asset5", "asset6", "asset7"]
    }
    assert asset_specs_by_key[AssetKey("asset1")] == AssetSpec(
        "asset1", tags={"foo": "fooval"}, group_name="default"
    )
    assert asset_specs_by_key[AssetKey("asset2")] == AssetSpec(
        "asset2", group_name="default", deps=[AssetDep("asset1")]
    )
    assert asset_specs_by_key[AssetKey("asset3")] == AssetSpec("asset3", group_name="default")
    assert asset_specs_by_key[AssetKey("asset4")] == AssetSpec("asset4", group_name="baz")
    assert asset_specs_by_key[AssetKey("asset5")] == AssetSpec(
        "asset5",
        group_name="default",
        tags={"biz": "boz"},
    )
    assert asset_specs_by_key[AssetKey("asset6")] == AssetSpec("asset6", group_name="blag")
    assert asset_specs_by_key[AssetKey("asset7")] == asset7._replace(group_name="default")


def test_asset_specs_different_partitions():
    asset1 = AssetSpec("asset1", partitions_def=StaticPartitionsDefinition(["a", "b"]))
    asset2 = AssetSpec("asset2", partitions_def=StaticPartitionsDefinition(["1", "2"]))
    Definitions.validate_loadable(Definitions(assets=[asset1, asset2]))


def test_asset_spec_dependencies_in_graph() -> None:
    upstream_asset = AssetSpec("upstream_asset")
    downstream_asset = AssetSpec("downstream_asset", deps=[upstream_asset])

    defs = Definitions(assets=[upstream_asset, downstream_asset])

    assert defs.get_asset_graph().asset_dep_graph["upstream"][downstream_asset.key] == {
        upstream_asset.key
    }


def test_invalid_partitions_subclass():
    class CustomPartitionsDefinition(PartitionsDefinition):
        def get_partition_keys(
            self,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Any = None,
        ) -> Sequence[str]:
            return ["a", "b", "c"]

    @asset(partitions_def=CustomPartitionsDefinition())
    def asset1():
        pass

    with pytest.warns(
        DeprecationWarning,
        match="custom PartitionsDefinition subclasses",
    ):
        Definitions.validate_loadable(Definitions(assets=[asset1]))


def test_hoist_automation_assets():
    @asset
    def foo():
        pass

    @asset
    def bar():
        pass

    @sensor(name="foo_sensor", target=foo)
    def foo_sensor():
        pass

    @schedule(name="bar_schedule", cron_schedule="* * * * *", target=bar)
    def bar_schedule():
        pass

    foo_job = define_asset_job("foo_job", selection=[foo])

    defs = Definitions(sensors=[foo_sensor], schedules=[bar_schedule], jobs=[foo_job])

    assert defs.get_assets_def(foo.key) == foo
    assert defs.get_assets_def(bar.key) == bar

    # We can define and execute asset jobs that reference assets only defined in targets
    assert defs.get_job_def(foo_job.name).execute_in_process().success


def test_definitions_failure_on_asset_job_resolve():
    @asset
    def asset_not_in_defs():
        pass

    invalid_job = define_asset_job("invalid_job", selection=[asset_not_in_defs])

    defs = Definitions(
        jobs=[invalid_job],
    )

    with pytest.raises(
        DagsterInvalidSubsetError, match="no AssetsDefinition objects supply these keys"
    ):
        Definitions.validate_loadable(defs)


def test_definitions_dedupe_reference_equality():
    """Test that Definitions objects correctly dedupe objects by
    reference equality.
    """

    @asset
    def the_asset():
        pass

    @asset_check(asset=the_asset)
    def the_check():
        return AssetCheckResult(passed=True)

    the_job = define_asset_job(name="the_job", selection="the_asset")

    @sensor(job=the_job)
    def the_sensor():
        pass

    @schedule(job=the_job, cron_schedule="* * * * *")
    def the_schedule():
        pass

    defs = Definitions(
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
                if not isinstance(assets_def, AssetChecksDefinition)
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
    assert len(defs.assets) == 2
    assert len(defs.asset_checks) == 2
    assert len(defs.jobs) == 2
    assert len(defs.sensors) == 2
    assert len(defs.schedules) == 2


def test_definitions_class_metadata():
    defs = Definitions(metadata={"foo": "bar"})
    assert defs.metadata == {"foo": MetadataValue.text("bar")}
    assert defs.get_repository_def().metadata == {"foo": MetadataValue.text("bar")}
