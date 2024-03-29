from collections import defaultdict
from typing import Sequence

import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInvalidDefinitionError,
    DailyPartitionsDefinition,
    GraphDefinition,
    IOManager,
    JobDefinition,
    OpDefinition,
    ResourceDefinition,
    SensorDefinition,
    SourceAsset,
    asset,
    build_schedule_from_partitioned_job,
    define_asset_job,
    executor,
    graph,
    in_process_executor,
    io_manager,
    job,
    logger,
    op,
    repository,
    resource,
    schedule,
    sensor,
)
from dagster._check import CheckError
from dagster._core.definitions.auto_materialize_sensor_definition import (
    AutoMaterializeSensorDefinition,
)
from dagster._core.definitions.decorators.asset_check_decorator import asset_check
from dagster._core.definitions.executor_definition import multi_or_in_process_executor
from dagster._core.definitions.partition import PartitionedConfig, StaticPartitionsDefinition
from dagster._core.errors import DagsterInvalidSubsetError
from dagster._loggers import default_loggers


def create_single_node_job(name, called):
    called[name] = called[name] + 1
    return JobDefinition(
        graph_def=GraphDefinition(
            name=name,
            node_defs=[
                OpDefinition(
                    name=name + "_op",
                    ins={},
                    outs={},
                    compute_fn=lambda *_args, **_kwargs: None,
                )
            ],
        )
    )


def test_repo_lazy_definition():
    called = defaultdict(int)

    @repository
    def lazy_repo():
        return {
            "jobs": {
                "foo": lambda: create_single_node_job("foo", called),
                "bar": lambda: create_single_node_job("bar", called),
            }
        }

    foo_job = lazy_repo.get_job("foo")
    assert isinstance(foo_job, JobDefinition)
    assert foo_job.name == "foo"

    assert "foo" in called
    assert called["foo"] == 1
    assert "bar" not in called

    bar_job = lazy_repo.get_job("bar")
    assert isinstance(bar_job, JobDefinition)
    assert bar_job.name == "bar"

    assert "foo" in called
    assert called["foo"] == 1
    assert "bar" in called
    assert called["bar"] == 1

    foo_job = lazy_repo.get_job("foo")
    assert isinstance(foo_job, JobDefinition)
    assert foo_job.name == "foo"

    assert "foo" in called
    assert called["foo"] == 1

    jobs = lazy_repo.get_all_jobs()

    assert set(["foo", "bar"]) == {job.name for job in jobs}


def test_dupe_op_repo_definition():
    @op(name="same")
    def noop():
        pass

    @op(name="same")
    def noop2():
        pass

    @repository
    def error_repo():
        return {
            "jobs": {
                "first": lambda: JobDefinition(
                    graph_def=GraphDefinition(name="first", node_defs=[noop])
                ),
                "second": lambda: JobDefinition(
                    graph_def=GraphDefinition(name="second", node_defs=[noop2])
                ),
            }
        }

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Conflicting definitions found in repository with name 'same'. Op/Graph definition"
            " names must be unique within a repository."
        ),
    ):
        error_repo.get_all_jobs()


def test_non_lazy_job_dict():
    called = defaultdict(int)

    @repository
    def some_repo():
        return [
            create_single_node_job("foo", called),
            create_single_node_job("bar", called),
        ]

    assert some_repo.get_job("foo").name == "foo"
    assert some_repo.get_job("bar").name == "bar"


def test_conflict():
    called = defaultdict(int)
    with pytest.raises(Exception, match="Duplicate job definition found for job 'foo'"):

        @repository
        def _some_repo():
            return [
                create_single_node_job("foo", called),
                create_single_node_job("foo", called),
            ]


def test_key_mismatch():
    called = defaultdict(int)

    @repository
    def some_repo():
        return {"jobs": {"foo": lambda: create_single_node_job("bar", called)}}

    with pytest.raises(Exception, match="name in JobDefinition does not match"):
        some_repo.get_job("foo")


def test_non_job_in_jobs():
    with pytest.raises(DagsterInvalidDefinitionError, match="all elements of list must be of type"):

        @repository
        def _some_repo():
            return ["not-a-job"]


def test_bad_schedule():
    @schedule(
        cron_schedule="* * * * *",
        job_name="foo",
    )
    def daily_foo(context):
        return {}

    with pytest.raises(
        # DagsterInvalidDefinitionError,
        Exception,
        match='targets job "foo" which was not found in this repository',
    ):

        @repository
        def _some_repo():
            return [daily_foo]


def test_bad_sensor():
    @sensor(
        job_name="foo",
    )
    def foo_sensor(_):
        return {}

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='targets job "foo" which was not found in this repository',
    ):

        @repository
        def _some_repo():
            return [foo_sensor]


def test_direct_schedule_target():
    @op
    def wow():
        return "wow"

    @graph
    def wonder():
        wow()

    @schedule(cron_schedule="* * * * *", job=wonder)
    def direct_schedule():
        return {}

    @repository
    def test():
        return [direct_schedule]

    assert test


def test_direct_schedule_unresolved_target():
    unresolved_job = define_asset_job("unresolved_job", selection="foo")

    @asset
    def foo():
        return None

    @schedule(cron_schedule="* * * * *", job=unresolved_job)
    def direct_schedule():
        return {}

    @repository
    def test():
        return [direct_schedule, foo]

    assert isinstance(test.get_job("unresolved_job"), JobDefinition)


def test_direct_sensor_target():
    @op
    def wow():
        return "wow"

    @graph
    def wonder():
        wow()

    @sensor(job=wonder)
    def direct_sensor(_):
        return {}

    @repository
    def test():
        return [direct_sensor]

    assert test


def test_direct_sensor_unresolved_target():
    unresolved_job = define_asset_job("unresolved_job", selection="foo")

    @asset
    def foo():
        return None

    @sensor(job=unresolved_job)
    def direct_sensor(_):
        return {}

    @repository
    def test():
        return [direct_sensor, foo]

    assert isinstance(test.get_job("unresolved_job"), JobDefinition)


def test_target_dupe_job():
    @op
    def wow():
        return "wow"

    @graph
    def wonder():
        wow()

    w_job = wonder.to_job()

    @sensor(job=w_job)
    def direct_sensor(_):
        return {}

    @repository
    def test():
        return [direct_sensor, w_job]

    assert test


def test_target_dupe_unresolved():
    unresolved_job = define_asset_job("unresolved_job", selection="foo")

    @asset
    def foo():
        return None

    @sensor(job=unresolved_job)
    def direct_sensor(_):
        return {}

    @repository
    def test():
        return [foo, direct_sensor, unresolved_job]

    assert isinstance(test.get_job("unresolved_job"), JobDefinition)


def test_bare_graph():
    @op
    def ok():
        return "sure"

    @graph
    def bare():
        ok()

    @repository
    def test():
        return [bare]

    # should get updated once "executable" exists
    assert test.get_job("bare")
    assert test.get_job("bare")


def test_unresolved_job():
    unresolved_job = define_asset_job("unresolved_job", selection="foo")

    @asset
    def foo():
        return None

    @repository
    def test():
        return [foo, unresolved_job]

    assert isinstance(test.get_job("unresolved_job"), JobDefinition)
    assert isinstance(test.get_job("unresolved_job"), JobDefinition)


def test_bare_graph_with_resources():
    @op(required_resource_keys={"stuff"})
    def needy(context):
        return context.resources.stuff

    @graph
    def bare():
        needy()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'stuff' required by op 'needy' was not provided",
    ):

        @repository
        def _test():
            return [bare]


def test_sensor_no_job_name():
    foo_system_sensor = SensorDefinition(name="foo", evaluation_fn=lambda x: x)

    @repository
    def foo_repo():
        return [foo_system_sensor]

    assert foo_repo.has_sensor_def("foo")


def test_job_with_partitions():
    @op
    def ok():
        return "sure"

    @graph
    def bare():
        ok()

    @repository
    def test():
        return [
            bare.to_job(
                resource_defs={},
                config=PartitionedConfig(
                    partitions_def=StaticPartitionsDefinition(["abc"]),
                    run_config_for_partition_key_fn=lambda _: {},
                ),
            )
        ]

    # do it twice to make sure we don't overwrite cache on second time
    assert test.has_job("bare")
    assert test.get_job("bare").partitions_def
    assert test.has_job("bare")
    assert test.get_job("bare").partitions_def


def test_dupe_graph_defs():
    @op
    def noop():
        pass

    @job(name="foo")
    def job_foo():
        noop()

    @graph(name="foo")
    def graph_foo():
        noop()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        # expect to change as migrate to graph/job
        match="Duplicate job definition found for job 'foo'",
    ):

        @repository
        def _job_collide():
            return [graph_foo, job_foo]

    def get_collision_repo():
        @repository
        def graph_collide():
            return [
                graph_foo.to_job(name="bar"),
                job_foo,
            ]

        return graph_collide

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Op/Graph definition names must be unique within a repository",
    ):
        get_collision_repo().get_all_jobs()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Op/Graph definition names must be unique within a repository",
    ):
        get_collision_repo().get_all_jobs()


def test_dupe_unresolved_job_defs():
    unresolved_job = define_asset_job("bar", selection="foo")

    @asset
    def foo():
        return None

    @op
    def the_op():
        pass

    @graph
    def graph_bar():
        the_op()

    bar = graph_bar.to_job(name="bar")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Duplicate job definition found for job 'bar'",
    ):

        @repository
        def _pipe_collide():
            return [foo, unresolved_job, bar]

    def get_collision_repo():
        @repository
        def graph_collide():
            return [
                foo,
                graph_bar.to_job(name="bar"),
                unresolved_job,
            ]

        return graph_collide

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Duplicate definition found for unresolved job 'bar'",
    ):
        get_collision_repo().get_all_jobs()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Duplicate definition found for unresolved job 'bar'",
    ):
        get_collision_repo().get_all_jobs()


def test_job_validation():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Object mapped to my_job is not an instance of JobDefinition or GraphDefinition.",
    ):

        @repository
        def _my_repo():
            return {"jobs": {"my_job": "blah"}}


def test_dict_jobs():
    @graph
    def my_graph():
        pass

    @repository
    def jobs():
        return {
            "jobs": {
                "my_graph": my_graph,
                "other_graph": my_graph.to_job(name="other_graph"),
                "tbd": define_asset_job("tbd", selection="*"),
            }
        }

    assert jobs.get_job("my_graph")
    assert jobs.get_job("other_graph")
    assert jobs.has_job("my_graph")
    assert jobs.get_job("my_graph")
    assert jobs.get_job("other_graph")
    assert jobs.has_job("tbd")
    assert jobs.get_job("tbd")


def test_lazy_jobs():
    @graph
    def my_graph():
        pass

    @repository
    def jobs():
        return {
            "jobs": {
                "my_graph": my_graph,
                "my_job": lambda: my_graph.to_job(name="my_job"),
                "other_job": lambda: my_graph.to_job(name="other_job"),
            }
        }

    assert jobs.get_job("my_graph")
    assert jobs.get_job("my_job")
    assert jobs.get_job("other_job")

    assert jobs.has_job("my_graph")
    assert jobs.get_job("my_job")
    assert jobs.get_job("other_job")


def test_lazy_graph():
    @graph
    def my_graph():
        pass

    @repository
    def jobs():
        return {
            "jobs": {
                "my_graph": lambda: my_graph,
            }
        }

    # Repository with a lazy graph can be constructed, but fails when you try to fetch it
    with pytest.raises(
        CheckError,
        match=(
            "Invariant failed. Description: Bad constructor for job my_graph: must return"
            " JobDefinition"
        ),
    ):
        assert jobs.get_job("my_graph")


def test_list_dupe_graph():
    @graph
    def foo():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Duplicate job definition found for graph 'foo'",
    ):

        @repository
        def _jobs():
            return [foo.to_job(name="foo"), foo]


def test_bad_coerce():
    @op(required_resource_keys={"x"})
    def foo():
        pass

    @graph
    def bar():
        foo()

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'x' required by op 'foo' was not provided",
    ):

        @repository
        def _fails():
            return {
                "jobs": {"bar": bar},
            }


def test_bad_resolve():
    with pytest.raises(DagsterInvalidSubsetError, match=r"AssetKey\(s\) \['foo'\] were selected"):

        @repository
        def _fails():
            return {"jobs": {"tbd": define_asset_job(name="tbd", selection="foo")}}


def test_source_assets():
    foo = SourceAsset(key=AssetKey("foo"))
    bar = SourceAsset(key=AssetKey("bar"))

    @repository
    def my_repo():
        return [foo, bar]

    all_assets = list(my_repo.asset_graph.assets_defs)
    assert len(all_assets) == 2
    assert {key.to_user_string() for a in all_assets for key in a.keys} == {"foo", "bar"}


def test_assets_checks():
    foo = SourceAsset(key=AssetKey("foo"))

    @asset_check(asset=foo)
    def foo_check():
        return True

    @repository
    def my_repo():
        return [foo, foo_check]

    assert my_repo.asset_checks_defs_by_key[next(iter(foo_check.check_keys))] == foo_check


def test_direct_assets():
    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        pass

    foo_resource = ResourceDefinition.hardcoded_resource("foo")
    foo = SourceAsset("foo", io_manager_def=the_manager, resource_defs={"foo": foo_resource})

    @asset(resource_defs={"foo": foo_resource})
    def asset1():
        pass

    @asset
    def asset2():
        pass

    @repository
    def my_repo():
        return [foo, asset1, asset2]

    assert len(my_repo.get_all_jobs()) == 1
    assert set(my_repo.get_all_jobs()[0].asset_layer.executable_asset_keys) == {
        AssetKey(["asset1"]),
        AssetKey(["asset2"]),
    }
    assert my_repo.get_all_jobs()[0].resource_defs["foo"] == foo_resource


def test_direct_assets_duplicate_keys():
    def make_asset():
        @asset
        def asset1():
            pass

        return asset1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"Duplicate asset key: AssetKey\(\['asset1'\]\)",
    ):

        @repository
        def my_repo():
            return [make_asset(), make_asset()]


def test_direct_asset_unsatified_resource():
    @asset(required_resource_keys={"a"})
    def asset1():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'a' required by op 'asset1' was not provided.",
    ):

        @repository
        def my_repo():
            return [asset1]


def test_direct_asset_unsatified_resource_transitive():
    @resource(required_resource_keys={"b"})
    def resource1():
        pass

    @asset(resource_defs={"a": resource1})
    def asset1():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'b' required by resource with key 'a' was not provided.",
    ):

        @repository
        def my_repo():
            return [asset1]


def test_source_asset_unsatisfied_resource():
    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by resource with key 'foo__io_manager' was not"
            " provided."
        ),
    ):

        @repository
        def the_repo():
            return [SourceAsset("foo", io_manager_def=the_manager)]


def test_source_asset_unsatisfied_resource_transitive():
    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        pass

    @resource(required_resource_keys={"bar"})
    def foo_resource():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'bar' required by resource with key 'foo' was not provided.",
    ):

        @repository
        def the_repo():
            return [
                SourceAsset(
                    "foo",
                    io_manager_def=the_manager,
                    resource_defs={"foo": foo_resource},
                )
            ]


def test_direct_asset_resource_conflicts():
    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def first():
        pass

    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")})
    def second():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):

        @repository
        def the_repo():
            return [first, second]


def test_source_asset_resource_conflicts():
    @asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def the_asset():
        pass

    @io_manager(required_resource_keys={"foo"})
    def the_manager():
        pass

    the_source = SourceAsset(
        key=AssetKey("the_key"),
        io_manager_def=the_manager,
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")},
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):

        @repository
        def the_repo():
            return [the_asset, the_source]

    other_source = SourceAsset(
        key=AssetKey("other_key"),
        io_manager_def=the_manager,
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("3")},
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):

        @repository
        def other_repo():
            return [other_source, the_source]


def test_assets_different_io_manager_defs():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert obj == 10

        def load_input(self, context):
            return 5

    the_manager_used = []

    @io_manager
    def the_manager():
        the_manager_used.append("yes")
        return MyIOManager()

    other_manager_used = []

    @io_manager
    def other_manager():
        other_manager_used.append("yes")
        return MyIOManager()

    @asset(io_manager_def=the_manager)
    def the_asset(the_source, other_source):
        return the_source + other_source

    @asset(io_manager_def=other_manager)
    def other_asset(the_source, other_source):
        return the_source + other_source

    the_source = SourceAsset(key=AssetKey("the_source"), io_manager_def=the_manager)

    other_source = SourceAsset(key=AssetKey("other_source"), io_manager_def=other_manager)

    @repository
    def the_repo():
        return [the_asset, other_asset, the_source, other_source]

    assert len(the_repo.get_all_jobs()) == 1
    assert the_repo.get_all_jobs()[0].execute_in_process().success
    assert len(the_manager_used) == 2
    assert len(other_manager_used) == 2


def _create_graph_with_name(name):
    @graph(name=name)
    def _the_graph():
        pass

    return _the_graph


def _create_job_with_name(name):
    @job(name=name)
    def _the_job():
        pass

    return _the_job


def _create_schedule_from_target(target):
    @schedule(job=target, cron_schedule="* * * * *")
    def _the_schedule():
        pass

    return _the_schedule


def _create_sensor_from_target(target):
    @sensor(job=target)
    def _the_sensor():
        pass

    return _the_sensor


def test_duplicate_graph_valid():
    the_graph = _create_graph_with_name("foo")

    # Providing the same graph to the repo and multiple schedules / sensors is valid
    @repository
    def the_repo_dupe_graph_valid():
        return [the_graph, _create_sensor_from_target(the_graph)]

    assert len(the_repo_dupe_graph_valid.get_all_jobs()) == 1


def test_duplicate_graph_target_invalid():
    the_graph = _create_graph_with_name("foo")
    other_graph = _create_graph_with_name("foo")
    # Different reference-equal graph provided to repo with same name, ensure error is thrown.
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "sensor '_the_sensor' targets graph 'foo', but a different graph with the same name was"
            " provided."
        ),
    ):

        @repository
        def the_repo_dupe_graph_invalid_sensor():
            return [the_graph, _create_sensor_from_target(other_graph)]

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "schedule '_the_schedule' targets graph 'foo', but a different graph with the same name"
            " was provided."
        ),
    ):

        @repository
        def the_repo_dupe_graph_invalid_schedule():
            return [the_graph, _create_schedule_from_target(other_graph)]


def test_duplicate_unresolved_job_valid():
    the_job = define_asset_job(name="foo")

    @asset
    def foo_asset():
        return 1

    # Providing the same graph to the repo and multiple schedules / sensors is valid
    @repository
    def the_repo_dupe_unresolved_job_valid():
        return [the_job, _create_sensor_from_target(the_job), foo_asset]

    # one job for the mega job
    assert len(the_repo_dupe_unresolved_job_valid.get_all_jobs()) == 2


def test_duplicate_unresolved_job_target_invalid():
    the_job = define_asset_job(name="foo")
    other_job = define_asset_job(name="foo", selection="foo")

    @asset
    def foo():
        return None

    # Different reference-equal jobs provided to repo with same name, ensure error is thrown.
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "sensor '_the_sensor' targets unresolved asset job 'foo', but a different unresolved"
            " asset job with the same name was provided."
        ),
    ):

        @repository
        def the_repo_dupe_graph_invalid_sensor():
            return [foo, the_job, _create_sensor_from_target(other_job)]

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "schedule '_the_schedule' targets unresolved asset job 'foo', but a different"
            " unresolved asset job with the same name was provided."
        ),
    ):

        @repository
        def the_repo_dupe_graph_invalid_schedule():
            return [foo, the_job, _create_schedule_from_target(other_job)]


def test_duplicate_job_target_valid():
    the_job = _create_job_with_name("foo")

    @repository
    def the_repo_dupe_job_valid():
        return [
            the_job,
            _create_schedule_from_target(the_job),
            _create_sensor_from_target(the_job),
        ]


def test_duplicate_job_target_invalid():
    the_job = _create_job_with_name("foo")
    other_job = _create_job_with_name("foo")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "sensor '_the_sensor' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @repository
        def the_repo_dupe_job_invalid_sensor():
            return [the_job, _create_sensor_from_target(other_job)]

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "schedule '_the_schedule' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @repository
        def the_repo_dupe_job_invalid_schedule():
            return [the_job, _create_schedule_from_target(other_job)]


def test_dupe_jobs_valid():
    the_job = _create_job_with_name("foo")

    @repository
    def the_repo_dupe_jobs_valid():
        return [
            the_job,
            _create_schedule_from_target(the_job),
            _create_sensor_from_target(the_job),
        ]


def test_dupe_jobs_invalid():
    the_job = _create_job_with_name("foo")
    other_job = _create_job_with_name("foo")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "schedule '_the_schedule' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @repository
        def the_repo_dupe_jobs_invalid_schedule():
            return [the_job, _create_schedule_from_target(other_job)]

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "sensor '_the_sensor' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @repository
        def the_repo_dupe_jobs_invalid_sensor():
            return [the_job, _create_sensor_from_target(other_job)]


def test_default_executor_repo():
    @repository(default_executor_def=in_process_executor)
    def the_repo():
        return []


def test_default_executor_assets_repo():
    @graph
    def no_executor_provided():
        pass

    @asset
    def the_asset():
        pass

    @repository(default_executor_def=in_process_executor)
    def the_repo():
        return [no_executor_provided, the_asset]

    assert the_repo.get_job("__ASSET_JOB").executor_def == in_process_executor

    assert the_repo.get_job("no_executor_provided").executor_def == in_process_executor


def test_default_executor_jobs():
    @asset
    def the_asset():
        pass

    unresolved_job = define_asset_job("asset_job", selection="*")

    @executor
    def custom_executor(_):
        pass

    @executor
    def other_custom_executor(_):
        pass

    @job(executor_def=custom_executor)
    def op_job_with_executor():
        pass

    @job
    def op_job_no_executor():
        pass

    @job(executor_def=multi_or_in_process_executor)
    def job_explicitly_specifies_default_executor():
        pass

    @job
    def the_job():
        pass

    @repository(default_executor_def=other_custom_executor)
    def the_repo():
        return [
            the_asset,
            op_job_with_executor,
            op_job_no_executor,
            unresolved_job,
            job_explicitly_specifies_default_executor,
        ]

    assert the_repo.get_job("asset_job").executor_def == other_custom_executor

    assert the_repo.get_job("op_job_with_executor").executor_def == custom_executor

    assert the_repo.get_job("op_job_no_executor").executor_def == other_custom_executor

    assert (
        the_repo.get_job("job_explicitly_specifies_default_executor").executor_def
        == multi_or_in_process_executor
    )


def test_list_load():
    @asset
    def asset1():
        return 1

    @asset
    def asset2():
        return 2

    source = SourceAsset(key=AssetKey("a_source_asset"))

    all_assets: Sequence[AssetsDefinition, SourceAsset] = [asset1, asset2, source]

    @repository
    def assets_repo():
        return [all_assets]

    assert len(assets_repo.get_all_jobs()) == 1
    assert set(assets_repo.get_all_jobs()[0].asset_layer.executable_asset_keys) == {
        AssetKey(["asset1"]),
        AssetKey(["asset2"]),
    }

    @op
    def op1():
        return 1

    @op
    def op2():
        return 1

    @job
    def job1():
        op1()

    @job
    def job2():
        op2()

    job_list = [job1, job2]

    @repository
    def job_repo():
        return [job_list]

    assert len(job_repo.get_all_jobs()) == len(job_list)

    @asset
    def asset3():
        return 3

    @op
    def op3():
        return 3

    @job
    def job3():
        op3()

    combo_list = [asset3, job3]

    @repository
    def combo_repo():
        return [combo_list]

    assert len(combo_repo.get_all_jobs()) == 2
    assert set(combo_repo.get_all_jobs()[0].asset_layer.executable_asset_keys) == {
        AssetKey(["asset3"]),
    }


def test_multi_nested_list():
    @asset
    def asset1():
        return 1

    @asset
    def asset2():
        return 2

    source = SourceAsset(key=AssetKey("a_source_asset"))

    layer_1: Sequence[AssetsDefinition, SourceAsset] = [asset2, source]
    layer_2 = [layer_1, asset1]

    with pytest.raises(DagsterInvalidDefinitionError, match="Bad return value from repository"):

        @repository
        def assets_repo():
            return [layer_2]


def test_default_executor_config():
    @asset
    def some_asset():
        pass

    @repository(default_executor_def=in_process_executor)
    def the_repo():
        # The config provided to the_job matches in_process_executor, but not the default executor.
        return [
            define_asset_job(
                "the_job",
                config={"execution": {"config": {"retries": {"enabled": {}}}}},
            ),
            some_asset,
        ]

    assert the_repo.get_job("the_job").executor_def == in_process_executor


def test_scheduled_partitioned_asset_job():
    partitions_def = DailyPartitionsDefinition(start_date="2022-06-06")

    @asset(partitions_def=partitions_def)
    def asset1(): ...

    @repository
    def repo():
        return [
            asset1,
            build_schedule_from_partitioned_job(
                define_asset_job("fdsjk", partitions_def=partitions_def)
            ),
        ]

    repo.load_all_definitions()


def test_default_loggers_repo():
    @logger
    def basic():
        pass

    @repository(default_logger_defs={"foo": basic})
    def the_repo():
        return []


def test_default_loggers_assets_repo():
    @graph
    def no_logger_provided():
        pass

    @asset
    def the_asset():
        pass

    @logger
    def basic():
        pass

    @repository(default_logger_defs={"foo": basic})
    def the_repo():
        return [no_logger_provided, the_asset]

    assert the_repo.get_job("__ASSET_JOB").loggers == {"foo": basic}

    assert the_repo.get_job("no_logger_provided").loggers == {"foo": basic}


def test_default_loggers_for_jobs():
    @asset
    def the_asset():
        pass

    unresolved_job = define_asset_job("asset_job", selection="*")

    @logger
    def custom_logger(_):
        pass

    @logger
    def other_custom_logger(_):
        pass

    @job(logger_defs={"bar": custom_logger})
    def job_with_loggers():
        pass

    @job
    def job_no_loggers():
        pass

    @job(logger_defs=default_loggers())
    def job_explicitly_specifies_default_loggers():
        pass

    @repository(default_logger_defs={"foo": other_custom_logger})
    def the_repo():
        return [
            the_asset,
            job_with_loggers,
            job_no_loggers,
            unresolved_job,
            job_explicitly_specifies_default_loggers,
        ]

    assert the_repo.get_job("asset_job").loggers == {"foo": other_custom_logger}

    assert the_repo.get_job("job_with_loggers").loggers == {"bar": custom_logger}

    assert the_repo.get_job("job_no_loggers").loggers == {"foo": other_custom_logger}

    assert the_repo.get_job("job_explicitly_specifies_default_loggers").loggers == default_loggers()


def test_default_loggers_keys_conflict():
    @logger
    def some_logger():
        pass

    @logger
    def other_logger():
        pass

    @job(logger_defs={"foo": some_logger})
    def the_job():
        pass

    @repository(default_logger_defs={"foo": other_logger})
    def the_repo():
        return [the_job]

    assert the_repo.get_job("the_job").loggers == {"foo": some_logger}


def test_base_jobs():
    @asset
    def asset1(): ...

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
    def asset2(): ...

    @asset(partitions_def=StaticPartitionsDefinition(["x", "y", "z"]))
    def asset3(): ...

    @repository
    def repo():
        return [asset1, asset2, asset3]

    assert sorted(repo.get_implicit_asset_job_names()) == ["__ASSET_JOB_0", "__ASSET_JOB_1"]
    assert repo.get_implicit_job_def_for_assets(
        [asset1.key, asset2.key]
    ).asset_layer.executable_asset_keys == {
        asset1.key,
        asset2.key,
    }
    assert repo.get_implicit_job_def_for_assets([asset2.key, asset3.key]) is None


def test_auto_materialize_sensors_do_not_conflict():
    @asset
    def asset1(): ...

    @asset
    def asset2(): ...

    @repository
    def repo():
        return [
            asset1,
            asset2,
            AutoMaterializeSensorDefinition("a", asset_selection=[asset1]),
            AutoMaterializeSensorDefinition("b", asset_selection=[asset2]),
        ]


def test_auto_materialize_sensors_incomplete_cover():
    @asset
    def asset1(): ...

    @asset
    def asset2(): ...

    @repository
    def repo():
        return [
            asset1,
            asset2,
            AutoMaterializeSensorDefinition("a", asset_selection=[asset1]),
        ]


def test_auto_materialize_sensors_conflict():
    @asset
    def asset1(): ...

    @asset
    def asset2(): ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Automation policy sensors '[ab]' and '[ab]' have overlapping asset selections: they both "
        "target 'asset1'. Each asset must only be targeted by one automation policy sensor.",
    ):

        @repository
        def repo():
            return [
                asset1,
                asset2,
                AutoMaterializeSensorDefinition("a", asset_selection=[asset1]),
                AutoMaterializeSensorDefinition("b", asset_selection=[asset1, asset2]),
            ]
