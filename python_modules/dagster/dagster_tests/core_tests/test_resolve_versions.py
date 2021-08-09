import hashlib

import pytest
from dagster import (
    Bool,
    DagsterInvariantViolationError,
    Float,
    IOManagerDefinition,
    In,
    Int,
    ModeDefinition,
    Output,
    OutputDefinition,
    String,
    composite_solid,
    dagster_type_loader,
    execute_pipeline,
    graph,
    io_manager,
    op,
    pipeline,
    resource,
    root_input_manager,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions import InputDefinition
from dagster.core.definitions.version_strategy import VersionStrategy
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.resolve_versions import join_and_hash, resolve_config_version
from dagster.core.storage.memoizable_io_manager import MemoizableIOManager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.test_utils import instance_for_test


class VersionedInMemoryIOManager(MemoizableIOManager):
    def __init__(self):
        self.values = {}

    def _get_keys(self, context):
        return (context.step_key, context.name, context.version)

    def handle_output(self, context, obj):
        keys = self._get_keys(context)
        self.values[keys] = obj

    def load_input(self, context):
        keys = self._get_keys(context.upstream_output)
        return self.values[keys]

    def has_output(self, context):
        keys = self._get_keys(context)
        return keys in self.values


def test_join_and_hash():
    assert join_and_hash("foo") == hashlib.sha1(b"foo").hexdigest()

    assert join_and_hash("foo", None, "bar") == None

    assert join_and_hash("foo", "bar") == hashlib.sha1(b"barfoo").hexdigest()

    assert join_and_hash("foo", "bar", "zab") == join_and_hash("zab", "bar", "foo")


def test_resolve_config_version():
    assert resolve_config_version(None) == join_and_hash()

    assert resolve_config_version({}) == join_and_hash()

    assert resolve_config_version({"a": "b", "c": "d"}) == join_and_hash(
        "a" + join_and_hash("b"), "c" + join_and_hash("d")
    )

    assert resolve_config_version({"a": "b", "c": "d"}) == resolve_config_version(
        {"c": "d", "a": "b"}
    )

    assert resolve_config_version({"a": {"b": "c"}, "d": "e"}) == join_and_hash(
        "a" + join_and_hash("b" + join_and_hash("c")), "d" + join_and_hash("e")
    )


@solid(version="42")
def versioned_solid_no_input(_):
    return 4


@solid(version="5")
def versioned_solid_takes_input(_, intput):
    return 2 * intput


def versioned_pipeline_factory(manager=VersionedInMemoryIOManager()):
    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="main",
                resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(manager)},
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def versioned_pipeline():
        versioned_solid_takes_input(versioned_solid_no_input())

    return versioned_pipeline


@solid
def solid_takes_input(_, intput):
    return 2 * intput


def partially_versioned_pipeline_factory(manager=VersionedInMemoryIOManager()):
    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="main",
                resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(manager)},
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def partially_versioned_pipeline():
        solid_takes_input(versioned_solid_no_input())

    return partially_versioned_pipeline


@solid
def basic_solid(_):
    return 5


@solid
def basic_takes_input_solid(_, intpt):
    return intpt * 4


@pipeline
def no_version_pipeline():
    basic_takes_input_solid(basic_solid())


def test_memoized_plan_no_memoized_results():
    with instance_for_test() as instance:
        versioned_pipeline = versioned_pipeline_factory()
        memoized_plan = create_execution_plan(versioned_pipeline, instance=instance)

        assert set(memoized_plan.step_keys_to_execute) == {
            "versioned_solid_no_input",
            "versioned_solid_takes_input",
        }


def test_memoized_plan_memoized_results():
    with instance_for_test() as instance:
        manager = VersionedInMemoryIOManager()

        versioned_pipeline = versioned_pipeline_factory(manager)
        plan = create_execution_plan(versioned_pipeline, instance=instance)
        resolved_run_config = ResolvedRunConfig.build(versioned_pipeline)

        # Affix a memoized value to the output
        step_output_handle = StepOutputHandle("versioned_solid_no_input", "result")
        step_output_version = plan.get_version_for_step_output_handle(step_output_handle)
        manager.values[
            (step_output_handle.step_key, step_output_handle.output_name, step_output_version)
        ] = 4

        memoized_plan = plan.build_memoized_plan(
            versioned_pipeline, resolved_run_config, instance=None
        )

        assert memoized_plan.step_keys_to_execute == ["versioned_solid_takes_input"]


def test_memoization_no_code_version_for_solid():
    with instance_for_test() as instance:
        partially_versioned_pipeline = partially_versioned_pipeline_factory()

        with pytest.raises(
            DagsterInvariantViolationError,
            match="While using memoization, version for solid 'solid_takes_input' was None. Please "
            "either provide a versioning strategy for your job, or provide a version using the "
            "solid decorator.",
        ):
            create_execution_plan(partially_versioned_pipeline, instance=instance)


def _get_ext_version(config_value):
    return join_and_hash(str(config_value))


@dagster_type_loader(String, loader_version="97", external_version_fn=_get_ext_version)
def InputHydration(_, _hello):
    return "Hello"


@usable_as_dagster_type(loader=InputHydration)
class CustomType(str):
    pass


def test_externally_loaded_inputs():
    for type_to_test, type_value in [
        (String, ("foo", "bar")),
        (Int, (int(42), int(46))),
        (Float, (float(5.42), float(5.45))),
        (Bool, (False, True)),
        (CustomType, ("bar", "baz")),
    ]:
        run_test_with_builtin_type(type_to_test, type_value)


def run_test_with_builtin_type(type_to_test, type_values):

    first_type_val, second_type_val = type_values
    manager = VersionedInMemoryIOManager()

    @solid(version="42", input_defs=[InputDefinition("_builtin_type", type_to_test)])
    def solid_ext_input(_builtin_type):
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(manager),
                },
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def my_pipeline():
        versioned_solid_takes_input(solid_ext_input())

    input_config = {"_builtin_type": first_type_val}
    run_config = {"solids": {"solid_ext_input": {"inputs": input_config}}}

    with instance_for_test() as instance:
        unmemoized_plan = create_execution_plan(
            my_pipeline,
            run_config=run_config,
            instance=instance,
        )

        assert len(unmemoized_plan.step_keys_to_execute) == 2

        step_output_handle = StepOutputHandle("solid_ext_input", "result")
        version = unmemoized_plan.get_version_for_step_output_handle(step_output_handle)

        manager.values[step_output_handle.step_key, step_output_handle.output_name, version] = 5

        memoized_plan = create_execution_plan(
            my_pipeline,
            run_config=run_config,
            instance=instance,
        )
        assert memoized_plan.step_keys_to_execute == ["versioned_solid_takes_input"]

        input_config["_builtin_type"] = second_type_val

        unmemoized_plan = create_execution_plan(
            my_pipeline,
            run_config=run_config,
            instance=instance,
        )

        assert len(unmemoized_plan.step_keys_to_execute) == 2


def test_memoized_plan_default_input_val():
    @solid(
        version="42",
        input_defs=[InputDefinition("_my_input", String, default_value="DEFAULTVAL")],
    )
    def solid_default_input(_my_input):
        pass

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(
                        VersionedInMemoryIOManager()
                    ),
                },
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def pipeline_default_value():
        solid_default_input()

    # Ensure that we can build a valid plan with a default input value.
    with instance_for_test() as instance:
        unmemoized_plan = create_execution_plan(pipeline_default_value, instance=instance)
        assert unmemoized_plan.step_keys_to_execute == ["solid_default_input"]


def test_memoized_plan_affected_by_resource_config():
    @solid(required_resource_keys={"my_resource"}, version="39")
    def solid_reqs_resource():
        pass

    @resource(version="42", config_schema={"foo": str})
    def basic():
        pass

    manager = VersionedInMemoryIOManager()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_resource": basic,
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(manager),
                },
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def my_pipeline():
        solid_reqs_resource()

    with instance_for_test() as instance:
        my_resource_config = {"foo": "bar"}
        run_config = {"resources": {"my_resource": {"config": my_resource_config}}}

        unmemoized_plan = create_execution_plan(
            my_pipeline, run_config=run_config, instance=instance
        )

        assert unmemoized_plan.step_keys_to_execute == ["solid_reqs_resource"]

        step_output_handle = StepOutputHandle("solid_reqs_resource", "result")
        version = unmemoized_plan.get_version_for_step_output_handle(step_output_handle)

        manager.values[step_output_handle.step_key, step_output_handle.output_name, version] = 5

        memoized_plan = create_execution_plan(my_pipeline, run_config=run_config, instance=instance)

        assert len(memoized_plan.step_keys_to_execute) == 0

        my_resource_config["foo"] = "baz"

        changed_config_plan = create_execution_plan(
            my_pipeline, run_config=run_config, instance=instance
        )

        assert changed_config_plan.step_keys_to_execute == ["solid_reqs_resource"]


def test_memoized_plan_custom_io_manager_key():
    manager = VersionedInMemoryIOManager()
    mgr_def = IOManagerDefinition.hardcoded_io_manager(manager)

    @solid(version="39", output_defs=[OutputDefinition(io_manager_key="my_key")])
    def solid_requires_io_manager():
        return Output(5)

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_key": mgr_def,
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def io_mgr_pipeline():
        solid_requires_io_manager()

    with instance_for_test() as instance:

        unmemoized_plan = create_execution_plan(io_mgr_pipeline, instance=instance)

        assert unmemoized_plan.step_keys_to_execute == ["solid_requires_io_manager"]

        step_output_handle = StepOutputHandle("solid_requires_io_manager", "result")
        version = unmemoized_plan.get_version_for_step_output_handle(step_output_handle)

        manager.values[(step_output_handle.step_key, step_output_handle.output_name, version)] = 5

        memoized_plan = create_execution_plan(io_mgr_pipeline, instance=instance)

        assert len(memoized_plan.step_keys_to_execute) == 0


def test_unmemoized_inner_solid():
    @solid
    def solid_no_version():
        pass

    @composite_solid
    def wrap():
        return solid_no_version()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="fakemode",
                resource_defs={
                    "fake": IOManagerDefinition.hardcoded_io_manager(VersionedInMemoryIOManager()),
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def wrap_pipeline():
        wrap()

    with instance_for_test() as instance:
        with pytest.raises(
            DagsterInvariantViolationError,
            match="While using memoization, version for solid 'solid_no_version' was None. Please "
            "either provide a versioning strategy for your job, or provide a version using the "
            "solid decorator.",
        ):
            create_execution_plan(wrap_pipeline, instance=instance)


def test_memoized_inner_solid():
    @solid(version="versioned")
    def solid_versioned():
        pass

    @composite_solid
    def wrap():
        return solid_versioned()

    mgr = VersionedInMemoryIOManager()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="fakemode",
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(mgr),
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def wrap_pipeline():
        wrap()

    with instance_for_test() as instance:
        unmemoized_plan = create_execution_plan(wrap_pipeline, instance=instance)
        step_output_handle = StepOutputHandle("wrap.solid_versioned", "result")
        assert unmemoized_plan.step_keys_to_execute == [step_output_handle.step_key]

        # Affix value to expected version for step output.
        step_output_version = unmemoized_plan.get_version_for_step_output_handle(step_output_handle)
        mgr.values[
            (step_output_handle.step_key, step_output_handle.output_name, step_output_version)
        ] = 4
        memoized_plan = unmemoized_plan.build_memoized_plan(
            wrap_pipeline, ResolvedRunConfig.build(wrap_pipeline), instance=None
        )
        assert len(memoized_plan.step_keys_to_execute) == 0


def test_configured_versions():
    @solid(version="5")
    def solid_to_configure():
        pass

    assert solid_to_configure.configured({}, name="solid_has_been_configured").version == "5"

    @resource(version="5")
    def resource_to_configure(_):
        pass

    assert resource_to_configure.configured({}).version == "5"


def test_memoized_plan_inits_resources_once():
    @solid(output_defs=[OutputDefinition(io_manager_key="foo")], version="foo")
    def foo_solid():
        pass

    @solid(output_defs=[OutputDefinition(io_manager_key="bar")], version="bar")
    def bar_solid():
        pass

    foo_capture = []
    bar_capture = []
    resource_dep_capture = []
    default_capture = []

    @io_manager(required_resource_keys={"my_resource"})
    def foo_manager():
        foo_capture.append("entered")
        return VersionedInMemoryIOManager()

    @io_manager(required_resource_keys={"my_resource"})
    def bar_manager():
        bar_capture.append("entered")
        return VersionedInMemoryIOManager()

    @io_manager
    def default_manager():
        default_capture.append("entered")
        return VersionedInMemoryIOManager()

    @resource
    def my_resource():
        resource_dep_capture.append("entered")
        return None

    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="fakemode",
                resource_defs={
                    "foo": foo_manager,
                    "bar": bar_manager,
                    "my_resource": my_resource,
                    "io_manager": default_manager,
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def wrap_pipeline():
        foo_solid()
        foo_solid.alias("another_foo")()
        bar_solid()
        bar_solid.alias("another_bar")()

    with instance_for_test() as instance:
        create_execution_plan(wrap_pipeline, instance=instance)

    assert len(foo_capture) == 1
    assert len(bar_capture) == 1
    assert len(resource_dep_capture) == 1
    assert len(default_capture) == 0


def test_memoized_plan_disable_memoization():
    @solid(version="hello")
    def my_solid():
        return 5

    mgr = VersionedInMemoryIOManager()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(mgr),
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def my_pipeline():
        my_solid()

    with instance_for_test() as instance:
        unmemoized_plan = create_execution_plan(my_pipeline, instance=instance)
        assert len(unmemoized_plan.step_keys_to_execute) == 1
        step_output_handle = StepOutputHandle("my_solid", "result")
        version = unmemoized_plan.get_version_for_step_output_handle(step_output_handle)
        mgr.values[(step_output_handle.step_key, step_output_handle.output_name, version)] = 5
        memoized_plan = create_execution_plan(my_pipeline, instance=instance)
        assert len(memoized_plan.step_keys_to_execute) == 0

        unmemoized_again = create_execution_plan(
            my_pipeline, instance=instance, tags={MEMOIZED_RUN_TAG: "false"}
        )
        assert len(unmemoized_again.step_keys_to_execute) == 1


def test_memoized_plan_root_input_manager():
    @root_input_manager(version="foo")
    def my_input_manager():
        return 5

    @solid(input_defs=[InputDefinition("x", root_manager_key="my_input_manager")], version="foo")
    def my_solid_takes_input(x):
        return x

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(
                        VersionedInMemoryIOManager()
                    ),
                    "my_input_manager": my_input_manager,
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def my_pipeline():
        my_solid_takes_input()

    with instance_for_test() as instance:
        plan = create_execution_plan(my_pipeline, instance=instance)
        assert (
            plan.get_version_for_step_output_handle(
                StepOutputHandle("my_solid_takes_input", "result")
            )
            is not None
        )


def test_memoized_plan_root_input_manager_input_config():
    @root_input_manager(version="foo", input_config_schema={"my_str": str})
    def my_input_manager():
        return 5

    @solid(input_defs=[InputDefinition("x", root_manager_key="my_input_manager")], version="foo")
    def my_solid_takes_input(x):
        return x

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(
                        VersionedInMemoryIOManager()
                    ),
                    "my_input_manager": my_input_manager,
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def my_pipeline():
        my_solid_takes_input()

    input_config = {"my_str": "foo"}
    run_config = {"solids": {"my_solid_takes_input": {"inputs": {"x": input_config}}}}
    with instance_for_test() as instance:
        plan = create_execution_plan(
            my_pipeline,
            instance=instance,
            run_config=run_config,
        )
        output_version = plan.get_version_for_step_output_handle(
            StepOutputHandle("my_solid_takes_input", "result")
        )

        assert output_version is not None

        input_config["my_str"] = "bar"

        plan = create_execution_plan(
            my_pipeline,
            instance=instance,
            run_config=run_config,
        )

        new_output_version = plan.get_version_for_step_output_handle(
            StepOutputHandle("my_solid_takes_input", "result")
        )

        # Ensure that after changing input config, the version changes.
        assert not new_output_version == output_version


def test_memoized_plan_root_input_manager_resource_config():
    @root_input_manager(version="foo", config_schema={"my_str": str})
    def my_input_manager():
        return 5

    @solid(input_defs=[InputDefinition("x", root_manager_key="my_input_manager")], version="foo")
    def my_solid_takes_input(x):
        return x

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(
                        VersionedInMemoryIOManager()
                    ),
                    "my_input_manager": my_input_manager,
                },
            ),
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def my_pipeline():
        my_solid_takes_input()

    resource_config = {"my_str": "foo"}
    run_config = {"resources": {"my_input_manager": {"config": resource_config}}}
    with instance_for_test() as instance:
        plan = create_execution_plan(
            my_pipeline,
            instance=instance,
            run_config=run_config,
        )
        output_version = plan.get_version_for_step_output_handle(
            StepOutputHandle("my_solid_takes_input", "result")
        )

        assert output_version is not None

        resource_config["my_str"] = "bar"

        plan = create_execution_plan(
            my_pipeline,
            instance=instance,
            run_config=run_config,
        )

        new_output_version = plan.get_version_for_step_output_handle(
            StepOutputHandle("my_solid_takes_input", "result")
        )

        # Ensure that after changing resource config, the version changes.
        assert not new_output_version == output_version


bad_str = "'well this doesn't work !'"


class BadSolidStrategy(VersionStrategy):
    def get_solid_version(self, solid_def):
        return bad_str

    def get_resource_version(self, resource_def):
        return "foo"


class BadResourceStrategy(VersionStrategy):
    def get_solid_version(self, solid_def):
        return "foo"

    def get_resource_version(self, resource_def):
        return bad_str


def get_basic_graph():
    @op
    def my_op():
        pass

    @graph
    def my_graph():
        my_op()

    return my_graph


def get_graph_reqs_resource():
    @op(required_resource_keys={"foo"})
    def my_op():
        pass

    @graph
    def my_graph():
        my_op()

    return my_graph


def get_graph_reqs_root_input_manager():
    @op(ins={"x": In(root_manager_key="my_key")})
    def my_op(x):
        return x

    @graph
    def my_graph():
        my_op()

    return my_graph


@pytest.mark.parametrize(
    "graph_for_test,strategy",
    [
        (get_basic_graph(), BadSolidStrategy()),
        (get_graph_reqs_resource(), BadResourceStrategy()),
        (get_graph_reqs_root_input_manager(), BadResourceStrategy()),
    ],
)
def test_bad_version_str(graph_for_test, strategy):
    @resource
    def my_resource():
        pass

    @root_input_manager
    def my_manager():
        pass

    with instance_for_test() as instance:
        my_job = graph_for_test.to_job(
            version_strategy=strategy,
            resource_defs={
                "io_manager": IOManagerDefinition.hardcoded_io_manager(
                    VersionedInMemoryIOManager()
                ),
                "my_key": my_manager,
                "foo": my_resource,
            },
        )

        with pytest.raises(
            DagsterInvariantViolationError, match=f"'{bad_str}' is not a valid version string."
        ):
            create_execution_plan(my_job, instance=instance)


def test_version_strategy_on_pipeline():
    @solid
    def my_solid():
        return 5

    class MyVersionStrategy(VersionStrategy):
        def get_solid_version(self, _):
            return "foo"

    @pipeline(
        version_strategy=MyVersionStrategy(),
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "io_manager": IOManagerDefinition.hardcoded_io_manager(
                        VersionedInMemoryIOManager()
                    )
                }
            )
        ],
    )
    def ten_pipeline():
        my_solid()

    with instance_for_test() as instance:
        execute_pipeline(ten_pipeline, instance=instance)

        memoized_plan = create_execution_plan(ten_pipeline, instance=instance)
        assert len(memoized_plan.step_keys_to_execute) == 0
