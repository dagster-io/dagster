import hashlib

import pytest

from dagster import (
    DagsterInstance,
    Field,
    ModeDefinition,
    Output,
    String,
    composite_solid,
    dagster_type_loader,
    pipeline,
    resource,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions import InputDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.execution.resolve_versions import (
    join_and_hash,
    resolve_config_version,
    resolve_resource_versions,
    resolve_step_output_versions,
    resolve_step_versions,
)
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.seven import mock


def test_join_and_hash():
    assert join_and_hash(["foo"]) == hashlib.sha1("foo".encode("utf-8")).hexdigest()

    assert join_and_hash(["foo", None, "bar"]) == None

    assert join_and_hash(["foo", "bar"]) == hashlib.sha1("barfoo".encode("utf-8")).hexdigest()

    assert join_and_hash(["foo", "bar", "zab"]) == join_and_hash(["zab", "bar", "foo"])


def test_resolve_config_version():
    assert resolve_config_version({}) == join_and_hash([])

    assert resolve_config_version({"a": "b", "c": "d"}) == join_and_hash(
        ["a" + join_and_hash(["b"]), "c" + join_and_hash(["d"])]
    )

    assert resolve_config_version({"a": "b", "c": "d"}) == resolve_config_version(
        {"c": "d", "a": "b"}
    )

    assert resolve_config_version({"a": {"b": "c"}, "d": "e"}) == join_and_hash(
        ["a" + join_and_hash(["b" + join_and_hash(["c"])]), "d" + join_and_hash(["e"])]
    )


@solid(version="42")
def versioned_solid_no_input(_):
    return 4


@solid(version="5")
def versioned_solid_takes_input(_, intput):
    return 2 * intput


@pipeline
def versioned_pipeline():
    return versioned_solid_takes_input(versioned_solid_no_input())


def versioned_pipeline_expected_step1_version():
    solid1_def_version = versioned_solid_no_input.version
    solid1_config_version = resolve_config_version(None)
    solid1_resources_version = join_and_hash([])
    solid1_version = join_and_hash(
        [solid1_def_version, solid1_config_version, solid1_resources_version]
    )
    return join_and_hash([solid1_version])


def versioned_pipeline_expected_step1_output_version():
    step1_version = versioned_pipeline_expected_step1_version()
    return join_and_hash([step1_version + "result"])


def versioned_pipeline_expected_step2_version():
    solid2_def_version = versioned_solid_takes_input.version
    solid2_config_version = resolve_config_version(None)
    solid2_resources_version = join_and_hash([])
    solid2_version = join_and_hash(
        [solid2_def_version, solid2_config_version, solid2_resources_version]
    )
    step1_outputs_hash = join_and_hash([versioned_pipeline_expected_step1_output_version()])

    step2_version = join_and_hash([step1_outputs_hash, solid2_version])
    return step2_version


def versioned_pipeline_expected_step2_output_version():
    step2_version = versioned_pipeline_expected_step2_version()
    return join_and_hash([step2_version + "result"])


def test_resolve_step_versions_no_external_dependencies():
    speculative_execution_plan = create_execution_plan(versioned_pipeline)
    versions = resolve_step_versions(speculative_execution_plan)

    assert (
        versions["versioned_solid_no_input.compute"] == versioned_pipeline_expected_step1_version()
    )

    assert (
        versions["versioned_solid_takes_input.compute"]
        == versioned_pipeline_expected_step2_version()
    )


def test_resolve_step_output_versions_no_external_dependencies():
    speculative_execution_plan = create_execution_plan(versioned_pipeline)
    versions = resolve_step_output_versions(
        speculative_execution_plan, run_config={}, mode="default"
    )

    assert (
        versions[StepOutputHandle("versioned_solid_no_input.compute", "result")]
        == versioned_pipeline_expected_step1_output_version()
    )
    assert (
        versions[StepOutputHandle("versioned_solid_takes_input.compute", "result")]
        == versioned_pipeline_expected_step2_output_version()
    )


def test_resolve_unmemoized_steps_no_stored_results():
    speculative_execution_plan = create_execution_plan(versioned_pipeline)

    instance = DagsterInstance.ephemeral()
    instance.get_addresses_for_step_output_versions = mock.MagicMock(return_value={})

    assert set(
        instance.resolve_unmemoized_steps(speculative_execution_plan, run_config={}, mode="default")
    ) == {"versioned_solid_no_input.compute", "versioned_solid_takes_input.compute"}


def test_resolve_unmemoized_steps_yes_stored_results():
    speculative_execution_plan = create_execution_plan(versioned_pipeline)
    step_output_handle = StepOutputHandle("versioned_solid_no_input.compute", "result")

    instance = DagsterInstance.ephemeral()
    instance.get_addresses_for_step_output_versions = mock.MagicMock(
        return_value={(versioned_pipeline.name, step_output_handle): "some_address"}
    )

    assert instance.resolve_unmemoized_steps(
        speculative_execution_plan, run_config={}, mode="default"
    ) == ["versioned_solid_takes_input.compute"]


def test_versioned_execution_plan_no_external_dependencies():  # TODO: flesh out this test once version storage has been implemented
    instance = DagsterInstance.ephemeral()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=versioned_pipeline, tags={MEMOIZED_RUN_TAG: "true"}
    )
    assert "versioned_solid_no_input.compute" in pipeline_run.step_keys_to_execute
    assert "versioned_solid_takes_input.compute" in pipeline_run.step_keys_to_execute
    assert len(pipeline_run.step_keys_to_execute) == 2


def _get_ext_version(config_value):
    return join_and_hash([str(config_value)])


@dagster_type_loader(String, loader_version="97", external_version_fn=_get_ext_version)
def InputHydration(_, _hello):
    return "Hello"


@usable_as_dagster_type(loader=InputHydration)
class CustomType(str):
    pass


@solid(version="42", input_defs=[InputDefinition("custom_type", CustomType)])
def versioned_solid_ext_input(_, custom_type):
    return custom_type * 4


@pipeline
def versioned_pipeline_ext_input():
    return versioned_solid_takes_input(versioned_solid_ext_input())


def test_resolve_step_versions_external_dependencies():
    run_config = {"solids": {"versioned_solid_ext_input": {"inputs": {"custom_type": "a"}}}}
    speculative_execution_plan = create_execution_plan(
        versioned_pipeline_ext_input, run_config=run_config,
    )

    versions = resolve_step_versions(speculative_execution_plan, run_config=run_config,)

    ext_input_version = join_and_hash(["a"])
    input_version = join_and_hash([InputHydration.loader_version + ext_input_version])

    solid1_def_version = versioned_solid_ext_input.version
    solid1_config_version = resolve_config_version(None)
    solid1_resources_version = join_and_hash([])
    solid1_version = join_and_hash(
        [solid1_def_version, solid1_config_version, solid1_resources_version]
    )

    step1_version = join_and_hash([input_version, solid1_version])
    assert versions["versioned_solid_ext_input.compute"] == step1_version

    output_version = join_and_hash([step1_version, "result"])
    hashed_input2 = join_and_hash([output_version])

    solid2_def_version = versioned_solid_takes_input.version
    solid2_config_version = resolve_config_version(None)
    solid2_resources_version = join_and_hash([])
    solid2_version = join_and_hash(
        [solid2_def_version, solid2_config_version, solid2_resources_version]
    )

    step2_version = join_and_hash([hashed_input2, solid2_version])
    assert versions["versioned_solid_takes_input.compute"] == step2_version


def test_external_dependencies():  # TODO: flesh out this test once version storage has been implemented
    instance = DagsterInstance.ephemeral()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=versioned_pipeline_ext_input,
        tags={MEMOIZED_RUN_TAG: "true"},
        run_config={"solids": {"versioned_solid_ext_input": {"inputs": {"custom_type": "a"}}}},
    )
    assert "versioned_solid_ext_input.compute" in pipeline_run.step_keys_to_execute
    assert "versioned_solid_takes_input.compute" in pipeline_run.step_keys_to_execute
    assert len(pipeline_run.step_keys_to_execute) == 2


@solid
def basic_solid(_):
    return 5


@solid
def basic_takes_input_solid(_, intpt):
    return intpt * 4


@pipeline
def default_version_pipeline():
    return basic_takes_input_solid(basic_solid())


def test_default_version():
    instance = DagsterInstance.ephemeral()
    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=default_version_pipeline, tags={MEMOIZED_RUN_TAG: "true"},
    )

    assert "basic_solid.compute" in pipeline_run.step_keys_to_execute
    assert "basic_takes_input_solid.compute" in pipeline_run.step_keys_to_execute
    assert len(pipeline_run.step_keys_to_execute) == 2


def test_step_keys_already_provided():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="step_keys_to_execute parameter "
        "cannot be used in conjunction with memoized pipeline runs.",
    ):
        instance = DagsterInstance.ephemeral()
        instance.create_run_for_pipeline(
            pipeline_def=default_version_pipeline,
            tags={MEMOIZED_RUN_TAG: "true"},
            step_keys_to_execute=["basic_takes_input_solid.compute"],
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
            "test_resource": {"config": {"input_str": "apple"},},
            "test_resource_no_version": {"config": {"input_str": "banana"}},
        }
    }
    environment_config = EnvironmentConfig.build(
        modes_pipeline, run_config=run_config, mode="fakemode",
    )

    resource_versions_by_key = resolve_resource_versions(
        environment_config, modes_pipeline.get_mode_definition("fakemode")
    )

    assert resource_versions_by_key["test_resource"] == join_and_hash(
        [resolve_config_version({"config": {"input_str": "apple"}}), test_resource.version]
    )

    assert resource_versions_by_key["test_resource_no_version"] == None

    assert resource_versions_by_key["test_resource_no_config"] == join_and_hash(
        [join_and_hash([]), "42"]
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
        versioned_modes_pipeline, run_config=run_config,
    )

    versions = resolve_step_versions(
        speculative_execution_plan, run_config=run_config, mode="fakemode"
    )

    solid_def_version = fake_solid_resources_versioned.version
    solid_config_version = resolve_config_version(None)
    environment_config = EnvironmentConfig.build(
        versioned_modes_pipeline, mode="fakemode", run_config=run_config
    )
    resource_versions_by_key = resolve_resource_versions(
        environment_config, versioned_modes_pipeline.get_mode_definition("fakemode")
    )
    solid_resources_version = join_and_hash(
        [
            resource_versions_by_key[resource_key]
            for resource_key in fake_solid_resources_versioned.required_resource_keys
        ]
    )
    solid_version = join_and_hash(
        [solid_def_version, solid_config_version, solid_resources_version]
    )

    step_version = join_and_hash([solid_version])

    assert versions["fake_solid_resources_versioned.compute"] == step_version


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
        return wrap.alias("do_stuff")()

    run_config = {
        "solids": {"do_stuff": {"config": {"override_str": "override"}}},
        "loggers": {"console": {"config": {"log_level": "ERROR"}}},
    }

    speculative_execution_plan = create_execution_plan(wrap_pipeline, run_config=run_config,)

    versions = resolve_step_versions(speculative_execution_plan, run_config=run_config)

    assert versions["do_stuff.scalar_config_solid.compute"] == None
