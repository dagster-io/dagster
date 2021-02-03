import hashlib

import pytest
from dagster import (
    Bool,
    DagsterInstance,
    Field,
    Float,
    Int,
    ModeDefinition,
    Output,
    String,
    composite_solid,
    dagster_type_loader,
    io_manager,
    pipeline,
    resource,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions import InputDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.resolve_versions import (
    join_and_hash,
    resolve_config_version,
    resolve_memoized_execution_plan,
    resolve_resource_versions,
)
from dagster.core.storage.memoizable_io_manager import MemoizableIOManager
from dagster.core.storage.tags import MEMOIZED_RUN_TAG


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


def io_manager_factory(manager):
    @io_manager
    def _io_manager_resource(_):
        return manager

    return _io_manager_resource


def test_join_and_hash():
    assert join_and_hash("foo") == hashlib.sha1(b"foo").hexdigest()

    assert join_and_hash("foo", None, "bar") == None

    assert join_and_hash("foo", "bar") == hashlib.sha1(b"barfoo").hexdigest()

    assert join_and_hash("foo", "bar", "zab") == join_and_hash("zab", "bar", "foo")


def test_resolve_config_version():
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


def versioned_pipeline_factory(manager=None):
    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="main",
                resource_defs=({"io_manager": io_manager_factory(manager)} if manager else {}),
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


def partially_versioned_pipeline_factory(manager=None):
    @pipeline(
        mode_defs=[
            ModeDefinition(
                name="main",
                resource_defs=({"io_manager": io_manager_factory(manager)} if manager else {}),
            )
        ],
        tags={MEMOIZED_RUN_TAG: "true"},
    )
    def partially_versioned_pipeline():
        solid_takes_input(versioned_solid_no_input())

    return partially_versioned_pipeline


def versioned_pipeline_expected_step1_version():
    solid1_def_version = versioned_solid_no_input.version
    solid1_config_version = resolve_config_version(None)
    solid1_resources_version = join_and_hash()
    solid1_version = join_and_hash(
        solid1_def_version, solid1_config_version, solid1_resources_version
    )
    return join_and_hash(solid1_version)


def versioned_pipeline_expected_step1_output_version():
    step1_version = versioned_pipeline_expected_step1_version()
    return join_and_hash(step1_version, "result")


def versioned_pipeline_expected_step2_version():
    solid2_def_version = versioned_solid_takes_input.version
    solid2_config_version = resolve_config_version(None)
    solid2_resources_version = join_and_hash()
    solid2_version = join_and_hash(
        solid2_def_version, solid2_config_version, solid2_resources_version
    )
    step1_outputs_hash = versioned_pipeline_expected_step1_output_version()

    step2_version = join_and_hash(step1_outputs_hash, solid2_version)
    return step2_version


def versioned_pipeline_expected_step2_output_version():
    step2_version = versioned_pipeline_expected_step2_version()
    return join_and_hash(step2_version + "result")


def test_resolve_step_versions_no_external_dependencies():
    versioned_pipeline = versioned_pipeline_factory()
    speculative_execution_plan = create_execution_plan(versioned_pipeline)
    versions = speculative_execution_plan.resolve_step_versions()

    assert versions["versioned_solid_no_input"] == versioned_pipeline_expected_step1_version()

    assert versions["versioned_solid_takes_input"] == versioned_pipeline_expected_step2_version()


def test_resolve_step_output_versions_no_external_dependencies():
    versioned_pipeline = versioned_pipeline_factory()
    speculative_execution_plan = create_execution_plan(
        versioned_pipeline, run_config={}, mode="main"
    )
    versions = speculative_execution_plan.resolve_step_output_versions()

    assert (
        versions[StepOutputHandle("versioned_solid_no_input", "result")]
        == versioned_pipeline_expected_step1_output_version()
    )
    assert (
        versions[StepOutputHandle("versioned_solid_takes_input", "result")]
        == versioned_pipeline_expected_step2_output_version()
    )


@solid
def basic_solid(_):
    return 5


@solid
def basic_takes_input_solid(_, intpt):
    return intpt * 4


@pipeline
def no_version_pipeline():
    basic_takes_input_solid(basic_solid())


def test_resolve_memoized_execution_plan_no_stored_results():
    versioned_pipeline = versioned_pipeline_factory(VersionedInMemoryIOManager())
    speculative_execution_plan = create_execution_plan(versioned_pipeline)

    memoized_execution_plan = resolve_memoized_execution_plan(speculative_execution_plan)

    assert set(memoized_execution_plan.step_keys_to_execute) == {
        "versioned_solid_no_input",
        "versioned_solid_takes_input",
    }


def test_resolve_memoized_execution_plan_yes_stored_results():
    manager = VersionedInMemoryIOManager()
    versioned_pipeline = versioned_pipeline_factory(manager)
    speculative_execution_plan = create_execution_plan(versioned_pipeline)
    step_output_handle = StepOutputHandle("versioned_solid_no_input", "result")
    step_output_version = speculative_execution_plan.resolve_step_output_versions()[
        step_output_handle
    ]
    manager.values[
        (step_output_handle.step_key, step_output_handle.output_name, step_output_version)
    ] = 4

    memoized_execution_plan = resolve_memoized_execution_plan(speculative_execution_plan)

    assert memoized_execution_plan.step_keys_to_execute == ["versioned_solid_takes_input"]

    expected_handle = StepOutputHandle(step_key="versioned_solid_no_input", output_name="result")

    assert (
        memoized_execution_plan.get_step_by_key("versioned_solid_takes_input")
        .step_input_dict["intput"]
        .source.step_output_handle
        == expected_handle
    )


def test_resolve_memoized_execution_plan_partial_versioning():
    manager = VersionedInMemoryIOManager()

    partially_versioned_pipeline = partially_versioned_pipeline_factory(manager)
    speculative_execution_plan = create_execution_plan(partially_versioned_pipeline)
    step_output_handle = StepOutputHandle("versioned_solid_no_input", "result")

    step_output_version = speculative_execution_plan.resolve_step_output_versions()[
        step_output_handle
    ]
    manager.values[
        (step_output_handle.step_key, step_output_handle.output_name, step_output_version)
    ] = 4

    assert resolve_memoized_execution_plan(speculative_execution_plan).step_keys_to_execute == [
        "solid_takes_input"
    ]


def _get_ext_version(config_value):
    return join_and_hash(str(config_value))


@dagster_type_loader(String, loader_version="97", external_version_fn=_get_ext_version)
def InputHydration(_, _hello):
    return "Hello"


@usable_as_dagster_type(loader=InputHydration)
class CustomType(str):
    pass


def test_externally_loaded_inputs():
    for type_to_test, loader_version, type_value in [
        (String, "String", "foo"),
        (Int, "Int", int(42)),
        (Float, "Float", float(5.42)),
        (Bool, "Bool", False),
        (CustomType, "97", "bar"),
    ]:
        run_test_with_builtin_type(type_to_test, loader_version, type_value)


def run_test_with_builtin_type(type_to_test, loader_version, type_value):
    @solid(version="42", input_defs=[InputDefinition("_builtin_type", type_to_test)])
    def versioned_solid_ext_input_builtin_type(_, _builtin_type):
        pass

    @pipeline
    def versioned_pipeline_ext_input_builtin_type():
        versioned_solid_takes_input(versioned_solid_ext_input_builtin_type())

    run_config = {
        "solids": {
            "versioned_solid_ext_input_builtin_type": {"inputs": {"_builtin_type": type_value}}
        }
    }
    speculative_execution_plan = create_execution_plan(
        versioned_pipeline_ext_input_builtin_type,
        run_config=run_config,
    )

    versions = speculative_execution_plan.resolve_step_versions()

    ext_input_version = join_and_hash(str(type_value))
    input_version = join_and_hash(loader_version + ext_input_version)

    solid1_def_version = versioned_solid_ext_input_builtin_type.version
    solid1_config_version = resolve_config_version(None)
    solid1_resources_version = join_and_hash()
    solid1_version = join_and_hash(
        solid1_def_version, solid1_config_version, solid1_resources_version
    )

    step1_version = join_and_hash(input_version, solid1_version)
    assert versions["versioned_solid_ext_input_builtin_type"] == step1_version

    output_version = join_and_hash(step1_version, "result")
    hashed_input2 = output_version

    solid2_def_version = versioned_solid_takes_input.version
    solid2_config_version = resolve_config_version(None)
    solid2_resources_version = join_and_hash()
    solid2_version = join_and_hash(
        solid2_def_version, solid2_config_version, solid2_resources_version
    )

    step2_version = join_and_hash(hashed_input2, solid2_version)
    assert versions["versioned_solid_takes_input"] == step2_version


@solid(
    version="42",
    input_defs=[InputDefinition("default_input", String, default_value="DEFAULTVAL")],
)
def versioned_solid_default_value(_, default_input):
    return default_input * 4


@pipeline
def versioned_pipeline_default_value():
    versioned_solid_default_value()


def test_resolve_step_versions_default_value():
    speculative_execution_plan = create_execution_plan(versioned_pipeline_default_value)
    versions = speculative_execution_plan.resolve_step_versions()

    input_version = join_and_hash(repr("DEFAULTVAL"))

    solid_def_version = versioned_solid_default_value.version
    solid_config_version = resolve_config_version(None)
    solid_resources_version = join_and_hash()
    solid_version = join_and_hash(solid_def_version, solid_config_version, solid_resources_version)

    step_version = join_and_hash(input_version, solid_version)
    assert versions["versioned_solid_default_value"] == step_version


def test_step_keys_already_provided():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="step_keys_to_execute parameter "
        "cannot be used in conjunction with memoized pipeline runs.",
    ):
        instance = DagsterInstance.ephemeral()
        instance.create_run_for_pipeline(
            pipeline_def=no_version_pipeline,
            tags={MEMOIZED_RUN_TAG: "true"},
            step_keys_to_execute=["basic_takes_input_solid"],
        )


@resource(config_schema={"input_str": Field(String)}, version="5")
def test_resource(context):
    return context.resource_config["input_str"]


@resource(config_schema={"input_str": Field(String)})
def test_resource_no_version(context):
    return context.resource_config["input_str"]


@resource(version="42")
def test_resource_no_config(_):
    return "Hello"


@solid(
    required_resource_keys={"test_resource", "test_resource_no_version", "test_resource_no_config"},
)
def fake_solid_resources(context):
    return (
        "solidified_"
        + context.resources.test_resource
        + context.resources.test_resource_no_version
        + context.resources.test_resource_no_config
    )


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="fakemode",
            resource_defs={
                "test_resource": test_resource,
                "test_resource_no_version": test_resource_no_version,
                "test_resource_no_config": test_resource_no_config,
            },
        ),
        ModeDefinition(
            name="fakemode2",
            resource_defs={
                "test_resource": test_resource,
                "test_resource_no_version": test_resource_no_version,
                "test_resource_no_config": test_resource_no_config,
            },
        ),
    ]
)
def modes_pipeline():
    fake_solid_resources()


def test_resource_versions():
    run_config = {
        "resources": {
            "test_resource": {
                "config": {"input_str": "apple"},
            },
            "test_resource_no_version": {"config": {"input_str": "banana"}},
        }
    }

    execution_plan = create_execution_plan(modes_pipeline, run_config=run_config, mode="fakemode")

    resource_versions_by_key = resolve_resource_versions(
        execution_plan.environment_config, execution_plan.pipeline.get_definition()
    )

    assert resource_versions_by_key["test_resource"] == join_and_hash(
        resolve_config_version({"config": {"input_str": "apple"}}), test_resource.version
    )

    assert resource_versions_by_key["test_resource_no_version"] == None

    assert resource_versions_by_key["test_resource_no_config"] == join_and_hash(
        join_and_hash(), "42"
    )


@solid(required_resource_keys={"test_resource", "test_resource_no_config"}, version="39")
def fake_solid_resources_versioned(context):
    return (
        "solidified_" + context.resources.test_resource + context.resources.test_resource_no_config
    )


@pipeline(
    mode_defs=[
        ModeDefinition(
            name="fakemode",
            resource_defs={
                "test_resource": test_resource,
                "test_resource_no_config": test_resource_no_config,
            },
        ),
    ]
)
def versioned_modes_pipeline():
    fake_solid_resources_versioned()


def test_step_versions_with_resources():
    run_config = {"resources": {"test_resource": {"config": {"input_str": "apple"}}}}
    speculative_execution_plan = create_execution_plan(
        versioned_modes_pipeline, run_config=run_config, mode="fakemode"
    )

    versions = speculative_execution_plan.resolve_step_versions()

    solid_def_version = fake_solid_resources_versioned.version
    solid_config_version = resolve_config_version(None)
    resource_versions_by_key = resolve_resource_versions(
        speculative_execution_plan.environment_config,
        speculative_execution_plan.pipeline.get_definition(),
    )
    solid_resources_version = join_and_hash(
        *[
            resource_versions_by_key[resource_key]
            for resource_key in fake_solid_resources_versioned.required_resource_keys
        ]
    )
    solid_version = join_and_hash(solid_def_version, solid_config_version, solid_resources_version)

    step_version = join_and_hash(solid_version)

    assert versions["fake_solid_resources_versioned"] == step_version


def test_step_versions_composite_solid():
    @solid(config_schema=Field(String, is_required=False))
    def scalar_config_solid(context):
        yield Output(context.solid_config)

    @composite_solid(
        config_schema={"override_str": Field(String)},
        config_fn=lambda cfg: {"scalar_config_solid": {"config": cfg["override_str"]}},
    )
    def wrap():
        return scalar_config_solid()

    @pipeline
    def wrap_pipeline():
        wrap.alias("do_stuff")()

    run_config = {
        "solids": {"do_stuff": {"config": {"override_str": "override"}}},
        "loggers": {"console": {"config": {"log_level": "ERROR"}}},
    }

    speculative_execution_plan = create_execution_plan(
        wrap_pipeline,
        run_config=run_config,
    )

    versions = speculative_execution_plan.resolve_step_versions()

    assert versions["do_stuff.scalar_config_solid"] == None
