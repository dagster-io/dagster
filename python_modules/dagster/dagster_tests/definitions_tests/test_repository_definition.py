from collections import defaultdict
from typing import TYPE_CHECKING

import dagster as dg
import pytest
from dagster import JobDefinition, ResourceDefinition, in_process_executor
from dagster._check import CheckError
from dagster._core.definitions.executor_definition import multi_or_in_process_executor

if TYPE_CHECKING:
    from collections.abc import Sequence


def create_single_node_job(name, called):
    called[name] = called[name] + 1
    return dg.JobDefinition(
        graph_def=dg.GraphDefinition(
            name=name,
            node_defs=[
                dg.OpDefinition(
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

    @dg.repository  # pyright: ignore[reportArgumentType]
    def lazy_repo():
        return {
            "jobs": {
                "foo": lambda: create_single_node_job("foo", called),
                "bar": lambda: create_single_node_job("bar", called),
            }
        }

    foo_job = lazy_repo.get_job("foo")
    assert isinstance(foo_job, dg.JobDefinition)
    assert foo_job.name == "foo"

    assert "foo" in called
    assert called["foo"] == 1
    assert "bar" not in called

    bar_job = lazy_repo.get_job("bar")
    assert isinstance(bar_job, dg.JobDefinition)
    assert bar_job.name == "bar"

    assert "foo" in called
    assert called["foo"] == 1
    assert "bar" in called
    assert called["bar"] == 1

    foo_job = lazy_repo.get_job("foo")
    assert isinstance(foo_job, dg.JobDefinition)
    assert foo_job.name == "foo"

    assert "foo" in called
    assert called["foo"] == 1

    jobs = lazy_repo.get_all_jobs()

    assert set(["foo", "bar"]) == {j.name for j in jobs}


def test_dupe_op_repo_definition():
    @dg.op(name="same")
    def noop():
        pass

    @dg.op(name="same")
    def noop2():
        pass

    @dg.repository  # pyright: ignore[reportArgumentType]
    def error_repo():
        return {
            "jobs": {
                "first": lambda: dg.JobDefinition(
                    graph_def=dg.GraphDefinition(name="first", node_defs=[noop])
                ),
                "second": lambda: dg.JobDefinition(
                    graph_def=dg.GraphDefinition(name="second", node_defs=[noop2])
                ),
            }
        }

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Conflicting definitions found in repository with name 'same'. Op/Graph definition"
            " names must be unique within a repository."
        ),
    ):
        error_repo.get_all_jobs()


def test_non_lazy_job_dict():
    called = defaultdict(int)

    @dg.repository
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

        @dg.repository
        def _some_repo():
            return [
                create_single_node_job("foo", called),
                create_single_node_job("foo", called),
            ]


def test_key_mismatch():
    called = defaultdict(int)

    @dg.repository  # pyright: ignore[reportArgumentType]
    def some_repo():
        return {"jobs": {"foo": lambda: create_single_node_job("bar", called)}}

    with pytest.raises(Exception, match="name in JobDefinition does not match"):
        some_repo.get_job("foo")


def test_non_job_in_jobs():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="all elements of list must be of type"
    ):

        @dg.repository  # pyright: ignore[reportArgumentType]
        def _some_repo():
            return ["not-a-job"]


def test_bad_schedule():
    @dg.schedule(
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

        @dg.repository
        def _some_repo():
            return [daily_foo]


def test_bad_sensor():
    @dg.sensor(  # pyright: ignore[reportArgumentType]
        job_name="foo",
    )
    def foo_sensor(_):
        return {}

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match='targets job "foo" which was not found in this repository',
    ):

        @dg.repository
        def _some_repo():
            return [foo_sensor]


def test_direct_schedule_target():
    @dg.op
    def wow():
        return "wow"

    @dg.graph
    def wonder():
        wow()

    @dg.schedule(cron_schedule="* * * * *", job=wonder)
    def direct_schedule():
        return {}

    @dg.repository
    def test():
        return [direct_schedule]

    assert test


def test_direct_schedule_unresolved_target():
    unresolved_job = dg.define_asset_job("unresolved_job", selection="foo")

    @dg.asset
    def foo():
        return None

    @dg.schedule(cron_schedule="* * * * *", job=unresolved_job)
    def direct_schedule():
        return {}

    @dg.repository
    def test():
        return [direct_schedule, foo]

    assert isinstance(test.get_job("unresolved_job"), dg.JobDefinition)


def test_direct_sensor_target():
    @dg.op
    def wow():
        return "wow"

    @dg.graph
    def wonder():
        wow()

    @dg.sensor(job=wonder)  # pyright: ignore[reportArgumentType]
    def direct_sensor(_):
        return {}

    @dg.repository
    def test():
        return [direct_sensor]

    assert test


def test_direct_sensor_unresolved_target():
    unresolved_job = dg.define_asset_job("unresolved_job", selection="foo")

    @dg.asset
    def foo():
        return None

    @dg.sensor(job=unresolved_job)  # pyright: ignore[reportArgumentType]
    def direct_sensor(_):
        return {}

    @dg.repository
    def test():
        return [direct_sensor, foo]

    assert isinstance(test.get_job("unresolved_job"), dg.JobDefinition)


def test_target_dupe_job():
    @dg.op
    def wow():
        return "wow"

    @dg.graph
    def wonder():
        wow()

    w_job = wonder.to_job()

    @dg.sensor(job=w_job)  # pyright: ignore[reportArgumentType]
    def direct_sensor(_):
        return {}

    @dg.repository
    def test():
        return [direct_sensor, w_job]

    assert test


def test_target_dupe_unresolved():
    unresolved_job = dg.define_asset_job("unresolved_job", selection="foo")

    @dg.asset
    def foo():
        return None

    @dg.sensor(job=unresolved_job)  # pyright: ignore[reportArgumentType]
    def direct_sensor(_):
        return {}

    @dg.repository
    def test():
        return [foo, direct_sensor, unresolved_job]

    assert isinstance(test.get_job("unresolved_job"), dg.JobDefinition)


def test_bare_graph():
    @dg.op
    def ok():
        return "sure"

    @dg.graph
    def bare():
        ok()

    @dg.repository
    def test():
        return [bare]

    # should get updated once "executable" exists
    assert test.get_job("bare")
    assert test.get_job("bare")


def test_unresolved_job():
    unresolved_job = dg.define_asset_job("unresolved_job", selection="foo")

    @dg.asset
    def foo():
        return None

    @dg.repository
    def test():
        return [foo, unresolved_job]

    assert isinstance(test.get_job("unresolved_job"), dg.JobDefinition)
    assert isinstance(test.get_job("unresolved_job"), dg.JobDefinition)


def test_bare_graph_with_resources():
    @dg.op(required_resource_keys={"stuff"})
    def needy(context):
        return context.resources.stuff

    @dg.graph
    def bare():
        needy()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'stuff' required by op 'needy' was not provided",
    ):

        @dg.repository
        def _test():
            return [bare]


def test_sensor_no_job_name():
    foo_system_sensor = dg.SensorDefinition(name="foo", evaluation_fn=lambda x: x)

    @dg.repository
    def foo_repo():
        return [foo_system_sensor]

    assert foo_repo.has_sensor_def("foo")


def test_job_with_partitions():
    @dg.op
    def ok():
        return "sure"

    @dg.graph
    def bare():
        ok()

    @dg.repository
    def test():
        return [
            bare.to_job(
                resource_defs={},
                config=dg.PartitionedConfig(
                    partitions_def=dg.StaticPartitionsDefinition(["abc"]),
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
    @dg.op
    def noop():
        pass

    @dg.job(name="foo")
    def job_foo():
        noop()

    @dg.graph(name="foo")
    def graph_foo():
        noop()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        # expect to change as migrate to graph/job
        match="Duplicate job definition found for job 'foo'",
    ):

        @dg.repository
        def _job_collide():
            return [graph_foo, job_foo]

    def get_collision_repo():
        @dg.repository
        def graph_collide():
            return [
                graph_foo.to_job(name="bar"),
                job_foo,
            ]

        return graph_collide

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Op/Graph definition names must be unique within a repository",
    ):
        get_collision_repo().get_all_jobs()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Op/Graph definition names must be unique within a repository",
    ):
        get_collision_repo().get_all_jobs()


def test_dupe_unresolved_job_defs():
    unresolved_job = dg.define_asset_job("bar", selection="foo")

    @dg.asset
    def foo():
        return None

    @dg.op
    def the_op():
        pass

    @dg.graph
    def graph_bar():
        the_op()

    bar = graph_bar.to_job(name="bar")

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Duplicate job definition found for job 'bar'",
    ):

        @dg.repository
        def _pipe_collide():
            return [foo, unresolved_job, bar]

    def get_collision_repo():
        @dg.repository
        def graph_collide():
            return [
                foo,
                graph_bar.to_job(name="bar"),
                unresolved_job,
            ]

        return graph_collide

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Duplicate definition found for unresolved job 'bar'",
    ):
        get_collision_repo().get_all_jobs()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Duplicate definition found for unresolved job 'bar'",
    ):
        get_collision_repo().get_all_jobs()


def test_job_validation():
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Object mapped to my_job is not an instance of JobDefinition or GraphDefinition.",
    ):

        @dg.repository  # pyright: ignore[reportArgumentType]
        def _my_repo():
            return {"jobs": {"my_job": "blah"}}


def test_dict_jobs():
    @dg.graph
    def my_graph():
        pass

    @dg.repository
    def jobs():
        return {
            "jobs": {
                "my_graph": my_graph,
                "other_graph": my_graph.to_job(name="other_graph"),
                "tbd": dg.define_asset_job("tbd", selection="*"),
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
    @dg.graph
    def my_graph():
        pass

    @dg.repository
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
    @dg.graph
    def my_graph():
        pass

    @dg.repository  # pyright: ignore[reportArgumentType]
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
            r"Invariant failed. Description: Bad constructor for job my_graph: must return"
            " JobDefinition"
        ),
    ):
        assert jobs.get_job("my_graph")


def test_list_dupe_graph():
    @dg.graph
    def foo():
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Duplicate job definition found for graph 'foo'",
    ):

        @dg.repository
        def _jobs():
            return [foo.to_job(name="foo"), foo]


def test_bad_coerce():
    @dg.op(required_resource_keys={"x"})
    def foo():
        pass

    @dg.graph
    def bar():
        foo()

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="resource with key 'x' required by op 'foo' was not provided",
    ):

        @dg.repository  # pyright: ignore[reportArgumentType]
        def _fails():
            return {
                "jobs": {"bar": bar},
            }


def test_bad_resolve():
    with pytest.raises(
        dg.DagsterInvalidSubsetError, match=r"AssetKey\(s\) \['foo'\] were selected"
    ):

        @dg.repository  # pyright: ignore[reportArgumentType]
        def _fails():
            return {"jobs": {"tbd": dg.define_asset_job(name="tbd", selection="foo")}}


def test_source_assets():
    foo = dg.SourceAsset(key=dg.AssetKey("foo"))
    bar = dg.SourceAsset(key=dg.AssetKey("bar"))

    @dg.repository
    def my_repo():
        return [foo, bar]

    all_assets = list(my_repo.asset_graph.assets_defs)
    assert len(all_assets) == 2
    assert {key.to_user_string() for a in all_assets for key in a.keys} == {"foo", "bar"}


def test_assets_checks():
    foo = dg.SourceAsset(key=dg.AssetKey("foo"))

    @dg.asset_check(asset=foo)  # pyright: ignore[reportArgumentType]
    def foo_check():
        return True

    @dg.repository
    def my_repo():
        return [foo, foo_check]

    assert my_repo.asset_checks_defs_by_key[next(iter(foo_check.check_keys))] == foo_check


def test_direct_assets():
    @dg.io_manager(required_resource_keys={"foo"})  # pyright: ignore[reportArgumentType]
    def the_manager():
        pass

    foo_resource = ResourceDefinition.hardcoded_resource("foo")
    foo = dg.SourceAsset("foo", io_manager_def=the_manager, resource_defs={"foo": foo_resource})

    @dg.asset(resource_defs={"foo": foo_resource})
    def asset1():
        pass

    @dg.asset
    def asset2():
        pass

    @dg.repository
    def my_repo():
        return [foo, asset1, asset2]

    assert len(my_repo.get_all_jobs()) == 1
    assert set(my_repo.get_all_jobs()[0].asset_layer.executable_asset_keys) == {
        dg.AssetKey(["asset1"]),
        dg.AssetKey(["asset2"]),
    }
    assert my_repo.get_all_jobs()[0].resource_defs["foo"] == foo_resource


def test_direct_assets_duplicate_keys():
    def make_asset():
        @dg.asset
        def asset1():
            pass

        return asset1

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Duplicate asset key: AssetKey\(\['asset1'\]\)",
    ):

        @dg.repository
        def my_repo():
            return [make_asset(), make_asset()]


def test_direct_asset_unsatified_resource():
    @dg.asset(required_resource_keys={"a"})
    def asset1():
        pass

    @dg.repository
    def my_repo():
        return [asset1]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"resource with key 'a' required by op 'asset1' was not provided.",
    ):
        my_repo.get_all_jobs()


def test_direct_asset_unsatified_resource_transitive():
    @dg.resource(required_resource_keys={"b"})
    def resource1():
        pass

    @dg.asset(resource_defs={"a": resource1})
    def asset1():
        pass

    @dg.repository
    def my_repo():
        return [asset1]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"resource with key 'b' required by resource with key 'a' was not provided.",
    ):
        my_repo.get_all_jobs()


def test_source_asset_unsatisfied_resource():
    @dg.io_manager(required_resource_keys={"foo"})  # pyright: ignore[reportArgumentType]
    def the_manager():
        pass

    @dg.repository
    def the_repo():
        return [dg.SourceAsset("foo", io_manager_def=the_manager)]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"resource with key 'foo' required by resource with key 'foo__io_manager' was not"
            " provided."
        ),
    ):
        the_repo.get_all_jobs()


def test_source_asset_unsatisfied_resource_transitive():
    @dg.io_manager(required_resource_keys={"foo"})  # pyright: ignore[reportArgumentType]
    def the_manager():
        pass

    @dg.resource(required_resource_keys={"bar"})
    def foo_resource():
        pass

    @dg.repository
    def the_repo():
        return [
            dg.SourceAsset(
                "foo",
                io_manager_def=the_manager,
                resource_defs={"foo": foo_resource},
            )
        ]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"resource with key 'bar' required by resource with key 'foo' was not provided.",
    ):
        the_repo.get_all_jobs()


def test_direct_asset_resource_conflicts():
    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def first():
        pass

    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")})
    def second():
        pass

    @dg.repository
    def the_repo():
        return [first, second]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):
        the_repo.get_all_jobs()


def test_source_asset_resource_conflicts():
    @dg.asset(resource_defs={"foo": ResourceDefinition.hardcoded_resource("1")})
    def the_asset():
        pass

    @dg.io_manager(required_resource_keys={"foo"})  # pyright: ignore[reportArgumentType]
    def the_manager():
        pass

    the_source = dg.SourceAsset(
        key=dg.AssetKey("the_key"),
        io_manager_def=the_manager,
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("2")},
    )

    @dg.repository
    def the_repo():
        return [the_asset, the_source]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):
        the_repo.get_all_jobs()

    other_source = dg.SourceAsset(
        key=dg.AssetKey("other_key"),
        io_manager_def=the_manager,
        resource_defs={"foo": ResourceDefinition.hardcoded_resource("3")},
    )

    @dg.repository
    def other_repo():
        return [other_source, the_source]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Conflicting versions of resource with key 'foo' were provided to different assets.",
    ):
        other_repo.get_all_jobs()


def test_assets_different_io_manager_defs():
    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert obj == 10

        def load_input(self, context):
            return 5

    the_manager_used = []

    @dg.io_manager
    def the_manager():
        the_manager_used.append("yes")
        return MyIOManager()

    other_manager_used = []

    @dg.io_manager
    def other_manager():
        other_manager_used.append("yes")
        return MyIOManager()

    @dg.asset(io_manager_def=the_manager)
    def the_asset(the_source, other_source):
        return the_source + other_source

    @dg.asset(io_manager_def=other_manager)
    def other_asset(the_source, other_source):
        return the_source + other_source

    the_source = dg.SourceAsset(key=dg.AssetKey("the_source"), io_manager_def=the_manager)

    other_source = dg.SourceAsset(key=dg.AssetKey("other_source"), io_manager_def=other_manager)

    @dg.repository
    def the_repo():
        return [the_asset, other_asset, the_source, other_source]

    assert len(the_repo.get_all_jobs()) == 1
    assert the_repo.get_all_jobs()[0].execute_in_process().success
    assert len(the_manager_used) == 2
    assert len(other_manager_used) == 2


def _create_graph_with_name(name):
    @dg.graph(name=name)
    def _the_graph():
        pass

    return _the_graph


def _create_job_with_name(name):
    @dg.job(name=name)
    def _the_job():
        pass

    return _the_job


def _create_schedule_from_target(target):
    @dg.schedule(job=target, cron_schedule="* * * * *")
    def _the_schedule():
        pass

    return _the_schedule


def _create_sensor_from_target(target):
    @dg.sensor(job=target)
    def _the_sensor():
        pass

    return _the_sensor


def test_duplicate_graph_valid():
    the_graph = _create_graph_with_name("foo")

    # Providing the same graph to the repo and multiple schedules / sensors is valid
    @dg.repository
    def the_repo_dupe_graph_valid():
        return [the_graph, _create_sensor_from_target(the_graph)]

    assert len(the_repo_dupe_graph_valid.get_all_jobs()) == 1


def test_duplicate_graph_target_invalid():
    the_graph = _create_graph_with_name("foo")
    other_graph = _create_graph_with_name("foo")
    # Different reference-equal graph provided to repo with same name, ensure error is thrown.
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"sensor '_the_sensor' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_graph_invalid_sensor():
            return [the_graph, _create_sensor_from_target(other_graph)]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"schedule '_the_schedule' targets job 'foo', but a different job with the same name"
            " was provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_graph_invalid_schedule():
            return [the_graph, _create_schedule_from_target(other_graph)]


def test_duplicate_unresolved_job_valid():
    the_job = dg.define_asset_job(name="foo")

    @dg.asset
    def foo_asset():
        return 1

    # Providing the same graph to the repo and multiple schedules / sensors is valid
    @dg.repository
    def the_repo_dupe_unresolved_job_valid():
        return [the_job, _create_sensor_from_target(the_job), foo_asset]

    # one job for the mega job
    assert len(the_repo_dupe_unresolved_job_valid.get_all_jobs()) == 2


def test_duplicate_unresolved_job_target_invalid():
    the_job = dg.define_asset_job(name="foo")
    other_job = dg.define_asset_job(name="foo", selection="foo")

    @dg.asset
    def foo():
        return None

    # Different reference-equal jobs provided to repo with same name, ensure error is thrown.
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"sensor '_the_sensor' targets unresolved asset job 'foo', but a different unresolved"
            " asset job with the same name was provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_graph_invalid_sensor():
            return [foo, the_job, _create_sensor_from_target(other_job)]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"schedule '_the_schedule' targets unresolved asset job 'foo', but a different"
            " unresolved asset job with the same name was provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_graph_invalid_schedule():
            return [foo, the_job, _create_schedule_from_target(other_job)]


def test_duplicate_job_target_valid():
    the_job = _create_job_with_name("foo")

    @dg.repository
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
        dg.DagsterInvalidDefinitionError,
        match=(
            r"sensor '_the_sensor' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_job_invalid_sensor():
            return [the_job, _create_sensor_from_target(other_job)]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"schedule '_the_schedule' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_job_invalid_schedule():
            return [the_job, _create_schedule_from_target(other_job)]


def test_dupe_jobs_valid():
    the_job = _create_job_with_name("foo")

    @dg.repository
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
        dg.DagsterInvalidDefinitionError,
        match=(
            r"schedule '_the_schedule' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_jobs_invalid_schedule():
            return [the_job, _create_schedule_from_target(other_job)]

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"sensor '_the_sensor' targets job 'foo', but a different job with the same name was"
            " provided."
        ),
    ):

        @dg.repository
        def the_repo_dupe_jobs_invalid_sensor():
            return [the_job, _create_sensor_from_target(other_job)]


def test_default_executor_repo():
    @dg.repository(default_executor_def=in_process_executor)
    def the_repo():
        return []


def test_default_executor_assets_repo():
    @dg.graph
    def no_executor_provided():
        pass

    @dg.asset
    def the_asset():
        pass

    @dg.repository(default_executor_def=in_process_executor)
    def the_repo():
        return [no_executor_provided, the_asset]

    assert the_repo.get_job("__ASSET_JOB").executor_def == dg.in_process_executor

    assert the_repo.get_job("no_executor_provided").executor_def == dg.in_process_executor


def test_default_executor_jobs():
    @dg.asset
    def the_asset():
        pass

    unresolved_job = dg.define_asset_job("asset_job", selection="*")

    @dg.executor  # pyright: ignore[reportCallIssue,reportArgumentType]
    def custom_executor(_):
        pass

    @dg.executor  # pyright: ignore[reportCallIssue,reportArgumentType]
    def other_custom_executor(_):
        pass

    @dg.job(executor_def=custom_executor)  # pyright: ignore[reportArgumentType]
    def op_job_with_executor():
        pass

    @dg.job
    def op_job_no_executor():
        pass

    @dg.job(executor_def=multi_or_in_process_executor)
    def job_explicitly_specifies_default_executor():
        pass

    @dg.job
    def the_job():
        pass

    @dg.repository(default_executor_def=other_custom_executor)  # pyright: ignore[reportArgumentType]
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
        == dg.multi_or_in_process_executor
    )


def test_list_load():
    @dg.asset
    def asset1():
        return 1

    @dg.asset
    def asset2():
        return 2

    source = dg.SourceAsset(key=dg.AssetKey("a_source_asset"))

    all_assets: Sequence[dg.AssetsDefinition, dg.SourceAsset] = [asset1, asset2, source]  # pyright: ignore[reportInvalidTypeArguments,reportAssignmentType]

    @dg.repository  # pyright: ignore[reportArgumentType]
    def assets_repo():
        return [all_assets]

    assert len(assets_repo.get_all_jobs()) == 1
    assert set(assets_repo.get_all_jobs()[0].asset_layer.executable_asset_keys) == {
        dg.AssetKey(["asset1"]),
        dg.AssetKey(["asset2"]),
    }

    @dg.op
    def op1():
        return 1

    @dg.op
    def op2():
        return 1

    @dg.job
    def job1():
        op1()

    @dg.job
    def job2():
        op2()

    job_list = [job1, job2]

    @dg.repository  # pyright: ignore[reportArgumentType]
    def job_repo():
        return [job_list]

    assert len(job_repo.get_all_jobs()) == len(job_list)

    @dg.asset
    def asset3():
        return 3

    @dg.op
    def op3():
        return 3

    @dg.job
    def job3():
        op3()

    combo_list = [asset3, job3]

    @dg.repository  # pyright: ignore[reportArgumentType]
    def combo_repo():
        return [combo_list]

    assert len(combo_repo.get_all_jobs()) == 2
    assert set(combo_repo.get_all_jobs()[0].asset_layer.executable_asset_keys) == {
        dg.AssetKey(["asset3"]),
    }


def test_multi_nested_list():
    @dg.asset
    def asset1():
        return 1

    @dg.asset
    def asset2():
        return 2

    source = dg.SourceAsset(key=dg.AssetKey("a_source_asset"))

    layer_1: Sequence[dg.AssetsDefinition, dg.SourceAsset] = [asset2, source]  # pyright: ignore[reportInvalidTypeArguments,reportAssignmentType]
    layer_2 = [layer_1, asset1]

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="Bad return value from repository"):

        @dg.repository  # pyright: ignore[reportArgumentType]
        def assets_repo():
            return [layer_2]


def test_default_executor_config():
    @dg.asset
    def some_asset():
        pass

    @dg.repository(default_executor_def=in_process_executor)
    def the_repo():
        # The config provided to the_job matches in_process_executor, but not the default executor.
        return [
            dg.define_asset_job(
                "the_job",
                config={"execution": {"config": {"retries": {"enabled": {}}}}},
            ),
            some_asset,
        ]

    assert the_repo.get_job("the_job").executor_def == dg.in_process_executor


def test_scheduled_partitioned_asset_job():
    partitions_def = dg.DailyPartitionsDefinition(start_date="2022-06-06")

    @dg.asset(partitions_def=partitions_def)
    def asset1(): ...

    @dg.repository
    def repo():
        return [
            asset1,
            dg.build_schedule_from_partitioned_job(
                dg.define_asset_job("fdsjk", partitions_def=partitions_def)
            ),
        ]

    repo.load_all_definitions()


def test_default_loggers_repo():
    @dg.logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def basic():
        pass

    @dg.repository(default_logger_defs={"foo": basic})  # pyright: ignore[reportArgumentType]
    def the_repo():
        return []


def test_default_loggers_assets_repo():
    @dg.graph
    def no_logger_provided():
        pass

    @dg.asset
    def the_asset():
        pass

    @dg.logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def basic():
        pass

    @dg.repository(default_logger_defs={"foo": basic})  # pyright: ignore[reportArgumentType]
    def the_repo():
        return [no_logger_provided, the_asset]

    assert the_repo.get_job("__ASSET_JOB").loggers == {"foo": basic}

    assert the_repo.get_job("no_logger_provided").loggers == {"foo": basic}


def test_default_loggers_for_jobs():
    @dg.asset
    def the_asset():
        pass

    unresolved_job = dg.define_asset_job("asset_job", selection="*")

    @dg.logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def custom_logger(_):
        pass

    @dg.logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def other_custom_logger(_):
        pass

    @dg.job(logger_defs={"bar": custom_logger})  # pyright: ignore[reportArgumentType]
    def job_with_loggers():
        pass

    @dg.job
    def job_no_loggers():
        pass

    @dg.job(logger_defs=dg.default_loggers())
    def job_explicitly_specifies_default_loggers():
        pass

    @dg.repository(default_logger_defs={"foo": other_custom_logger})  # pyright: ignore[reportArgumentType]
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

    assert (
        the_repo.get_job("job_explicitly_specifies_default_loggers").loggers == dg.default_loggers()
    )


def test_default_loggers_keys_conflict():
    @dg.logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def some_logger():
        pass

    @dg.logger  # pyright: ignore[reportCallIssue,reportArgumentType]
    def other_logger():
        pass

    @dg.job(logger_defs={"foo": some_logger})  # pyright: ignore[reportArgumentType]
    def the_job():
        pass

    @dg.repository(default_logger_defs={"foo": other_logger})  # pyright: ignore[reportArgumentType]
    def the_repo():
        return [the_job]

    assert the_repo.get_job("the_job").loggers == {"foo": some_logger}


def test_implicit_asset_job():
    @dg.asset
    def asset1(): ...

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
    def asset2(): ...

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["x", "y", "z"]))
    def asset3(): ...

    @dg.repository
    def repo():
        return [asset1, asset2, asset3]

    job_def = repo.get_implicit_global_asset_job_def()
    assert job_def.name == "__ASSET_JOB"
    assert job_def.asset_layer.executable_asset_keys == {asset1.key, asset2.key, asset3.key}


def test_auto_materialize_sensors_do_not_conflict():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    @dg.repository
    def repo():
        return [
            asset1,
            asset2,
            dg.AutomationConditionSensorDefinition("a", target=[asset1]),
            dg.AutomationConditionSensorDefinition("b", target=[asset2]),
        ]


def test_auto_materialize_sensors_incomplete_cover():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    @dg.repository
    def repo():
        return [
            asset1,
            asset2,
            dg.AutomationConditionSensorDefinition("a", target=[asset1]),
        ]


def test_auto_materialize_sensors_conflict():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=r"Automation policy sensors '[ab]' and '[ab]' have overlapping asset selections: they both "
        "target 'asset1'. Each asset must only be targeted by one automation policy sensor.",
    ):

        @dg.repository
        def repo():
            return [
                asset1,
                asset2,
                dg.AutomationConditionSensorDefinition("a", target=[asset1]),
                dg.AutomationConditionSensorDefinition("b", target=[asset1, asset2]),
            ]


def test_external_job_assets() -> None:
    @dg.asset
    def my_asset():
        pass

    my_job = JobDefinition.for_external_job(
        asset_keys=[my_asset.key],
        name="my_job",
        metadata={"foo": "bar"},
        tags={"baz": "qux"},
    )

    assert set(my_job.asset_layer.external_job_asset_keys) == {my_asset.key}
    assert my_job.metadata == {"foo": dg.TextMetadataValue("bar")}
    assert my_job.tags == {"baz": "qux"}

    @dg.repository
    def repo():
        return [my_job, my_asset]

    assert repo.assets_defs_by_key[my_asset.key] == my_asset
