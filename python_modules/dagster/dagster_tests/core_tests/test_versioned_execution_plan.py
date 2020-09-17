import hashlib

import pytest

from dagster import (
    DagsterInstance,
    String,
    dagster_type_loader,
    pipeline,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions import InputDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.resolve_versions import (
    join_and_hash,
    resolve_config_version,
    resolve_step_versions,
)
from dagster.core.storage.tags import MEMOIZED_RUN_TAG


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


def test_resolve_step_versions_no_external_dependencies():
    versions = resolve_step_versions(versioned_pipeline)
    solid1_hash = join_and_hash([versioned_solid_no_input.version])
    output1_hash = join_and_hash([solid1_hash + "result"])
    outputs_hash = join_and_hash([output1_hash])
    solid2_hash = join_and_hash([outputs_hash, versioned_solid_takes_input.version])

    assert versions["versioned_solid_no_input.compute"] == solid1_hash

    assert versions["versioned_solid_takes_input.compute"] == solid2_hash


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
    versions = resolve_step_versions(
        versioned_pipeline_ext_input,
        run_config={"solids": {"versioned_solid_ext_input": {"inputs": {"custom_type": "a"}}}},
    )

    ext_input_version = join_and_hash(["a"])
    input_version = join_and_hash([InputHydration.loader_version + ext_input_version])
    step_version1 = join_and_hash([input_version, versioned_solid_ext_input.version])
    assert versions["versioned_solid_ext_input.compute"] == step_version1

    output_version = join_and_hash([step_version1, "result"])
    hashed_input2 = join_and_hash([output_version])
    step_version2 = join_and_hash([hashed_input2, versioned_solid_takes_input.version])
    assert versions["versioned_solid_takes_input.compute"] == step_version2


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
