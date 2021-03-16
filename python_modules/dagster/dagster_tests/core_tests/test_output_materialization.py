import json

import pytest
from dagster import (
    AssetMaterialization,
    DagsterEventType,
    DagsterInvalidConfigError,
    InputDefinition,
    Int,
    Output,
    OutputDefinition,
    PipelineDefinition,
    String,
    dagster_type_materializer,
    execute_pipeline,
    lambda_solid,
    solid,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.step import StepKind
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.dagster_type import create_any_type
from dagster.utils.test import get_temp_file_name, get_temp_file_names


def single_int_output_pipeline():
    @lambda_solid(output_def=OutputDefinition(Int))
    def return_one():
        return 1

    return PipelineDefinition(name="single_int_output_pipeline", solid_defs=[return_one])


def single_string_output_pipeline():
    @lambda_solid(output_def=OutputDefinition(String))
    def return_foo():
        return "foo"

    return PipelineDefinition(name="single_string_output_pipeline", solid_defs=[return_foo])


def multiple_output_pipeline():
    @solid(output_defs=[OutputDefinition(Int, "number"), OutputDefinition(String, "string")])
    def return_one_and_foo(_context):
        yield Output(1, "number")
        yield Output("foo", "string")

    return PipelineDefinition(name="multiple_output_pipeline", solid_defs=[return_one_and_foo])


def single_int_named_output_pipeline():
    @lambda_solid(output_def=OutputDefinition(Int, name="named"))
    def return_named_one():
        return Output(1, "named")

    return PipelineDefinition(
        name="single_int_named_output_pipeline", solid_defs=[return_named_one]
    )


def no_input_no_output_pipeline():
    @solid(output_defs=[])
    def take_nothing_return_nothing(_context):
        pass

    return PipelineDefinition(
        name="no_input_no_output_pipeline", solid_defs=[take_nothing_return_nothing]
    )


def one_input_no_output_pipeline():
    @solid(input_defs=[InputDefinition("dummy")], output_defs=[])
    def take_input_return_nothing(_context, **_kwargs):
        pass

    return PipelineDefinition(
        name="one_input_no_output_pipeline", solid_defs=[take_input_return_nothing]
    )


def test_basic_json_default_output_config_schema():
    env = EnvironmentConfig.build(
        single_int_output_pipeline(),
        {"solids": {"return_one": {"outputs": [{"result": {"json": {"path": "foo"}}}]}}},
    )

    assert env.solids["return_one"]
    assert env.solids["return_one"].outputs.type_materializer_specs == [
        {"result": {"json": {"path": "foo"}}}
    ]


def test_basic_json_named_output_config_schema():
    env = EnvironmentConfig.build(
        single_int_named_output_pipeline(),
        {"solids": {"return_named_one": {"outputs": [{"named": {"json": {"path": "foo"}}}]}}},
    )

    assert env.solids["return_named_one"]
    assert env.solids["return_named_one"].outputs.type_materializer_specs == [
        {"named": {"json": {"path": "foo"}}}
    ]


def test_basic_json_misnamed_output_config_schema():
    with pytest.raises(DagsterInvalidConfigError) as exc_context:
        EnvironmentConfig.build(
            single_int_named_output_pipeline(),
            {
                "solids": {
                    "return_named_one": {"outputs": [{"wrong_name": {"json": {"path": "foo"}}}]}
                }
            },
        )

    assert len(exc_context.value.errors) == 1
    assert 'Error 1: Received unexpected config entry "wrong_name"' in exc_context.value.message
    assert "at path root:solids:return_named_one:outputs[0]" in exc_context.value.message


def test_no_outputs_no_inputs_config_schema():
    assert EnvironmentConfig.build(no_input_no_output_pipeline())

    with pytest.raises(DagsterInvalidConfigError) as exc_context:
        EnvironmentConfig.build(no_input_no_output_pipeline(), {"solids": {"return_one": {}}})

    assert len(exc_context.value.errors) == 1
    assert (
        'Error 1: Received unexpected config entry "return_one" at path root:solids'
        in exc_context.value.message
    )


def test_no_outputs_one_input_config_schema():
    assert EnvironmentConfig.build(
        one_input_no_output_pipeline(),
        {"solids": {"take_input_return_nothing": {"inputs": {"dummy": {"value": "value"}}}}},
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_context:
        EnvironmentConfig.build(
            one_input_no_output_pipeline(),
            {
                "solids": {
                    "take_input_return_nothing": {
                        "inputs": {"dummy": {"value": "value"}},
                        "outputs": {},
                    }
                }
            },
        )

    assert len(exc_context.value.errors) == 1
    exp_msg = 'Error 1: Received unexpected config entry "outputs" at path root:solids:take_input_return_nothing'
    assert exp_msg in exc_context.value.message


def test_basic_int_json_materialization():
    with get_temp_file_name() as filename:
        result = execute_pipeline(
            single_int_output_pipeline(),
            {"solids": {"return_one": {"outputs": [{"result": {"json": {"path": filename}}}]}}},
        )

        assert result.success

        with open(filename, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


def test_basic_materialization_event():
    with get_temp_file_name() as filename:
        result = execute_pipeline(
            single_int_output_pipeline(),
            {"solids": {"return_one": {"outputs": [{"result": {"json": {"path": filename}}}]}}},
        )

        assert result.success
        solid_result = result.result_for_solid("return_one")
        step_events = solid_result.step_events_by_kind[StepKind.COMPUTE]
        mat_event = list(
            filter(lambda de: de.event_type == DagsterEventType.ASSET_MATERIALIZATION, step_events)
        )[0]

        mat = mat_event.event_specific_data.materialization

        assert len(mat.metadata_entries) == 1
        assert mat.metadata_entries[0].path
        path = mat.metadata_entries[0].entry_data.path

        with open(path, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


def test_basic_string_json_materialization():
    pipeline = single_string_output_pipeline()

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            pipeline,
            {"solids": {"return_foo": {"outputs": [{"result": {"json": {"path": filename}}}]}}},
        )

        assert result.success

        with open(filename, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": "foo"}


def test_basic_int_and_string_json_materialization():

    pipeline = multiple_output_pipeline()

    with get_temp_file_names(2) as file_tuple:
        filename_one, filename_two = file_tuple  # pylint: disable=E0632
        result = execute_pipeline(
            pipeline,
            {
                "solids": {
                    "return_one_and_foo": {
                        "outputs": [
                            {"string": {"json": {"path": filename_one}}},
                            {"number": {"json": {"path": filename_two}}},
                        ]
                    }
                }
            },
        )

        assert result.success

        with open(filename_one, "r") as ff_1:
            value = json.loads(ff_1.read())
            assert value == {"value": "foo"}

        with open(filename_two, "r") as ff_2:
            value = json.loads(ff_2.read())
            assert value == {"value": 1}


def read_file_contents(path):
    with open(path, "r") as ff:
        return ff.read()


def test_basic_int_and_string_json_multiple_materialization():

    pipeline = multiple_output_pipeline()

    with get_temp_file_names(4) as file_tuple:
        # False positive for unbalanced tuple unpacking
        # pylint: disable=E0632
        filename_one, filename_two, filename_three, filename_four = file_tuple
        result = execute_pipeline(
            pipeline,
            {
                "solids": {
                    "return_one_and_foo": {
                        "outputs": [
                            {"string": {"json": {"path": filename_one}}},
                            {"string": {"json": {"path": filename_two}}},
                            {"number": {"json": {"path": filename_three}}},
                            {"number": {"json": {"path": filename_four}}},
                        ]
                    }
                }
            },
        )

        assert result.success

        with open(filename_one, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": "foo"}

        with open(filename_two, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": "foo"}

        with open(filename_three, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}

        with open(filename_four, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


def assert_step_before(steps, first_step, second_step):
    step_keys = [step.key for step in steps]
    assert step_keys.index(first_step) < step_keys.index(second_step)


def assert_plan_topological_level(steps, step_nums, step_keys):
    assert set(steps[step_num].key for step_num in step_nums) == set(step_keys)


def test_basic_int_json_multiple_materializations():
    pipeline = single_int_output_pipeline()

    with get_temp_file_names(2) as file_tuple:
        filename_one, filename_two = file_tuple  # pylint: disable=E0632
        result = execute_pipeline(
            pipeline,
            {
                "solids": {
                    "return_one": {
                        "outputs": [
                            {"result": {"json": {"path": filename_one}}},
                            {"result": {"json": {"path": filename_two}}},
                        ]
                    }
                }
            },
        )

        assert result.success

        with open(filename_one, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}

        with open(filename_two, "r") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


@dagster_type_materializer(Int)
def yield_two_materializations(*_args, **_kwargs):
    yield AssetMaterialization("first")
    yield AssetMaterialization("second")


def test_basic_yield_multiple_materializations():
    SomeDagsterType = create_any_type(name="SomeType", materializer=yield_two_materializations)

    @lambda_solid(output_def=OutputDefinition(SomeDagsterType))
    def return_one():
        return 1

    pipeline_def = PipelineDefinition(name="single_int_output_pipeline", solid_defs=[return_one])
    result = execute_pipeline(
        pipeline_def, run_config={"solids": {"return_one": {"outputs": [{"result": 2}]}}}
    )
    assert result.success

    event_types = [event.event_type_value for event in result.event_list]
    assert 2 == (
        sum(
            [
                True
                for event_type in event_types
                if event_type == DagsterEventType.ASSET_MATERIALIZATION.value
            ]
        )
    )


@dagster_type_materializer(Int)
def return_int(*_args, **_kwargs):
    return 1


def test_basic_bad_output_materialization():
    SomeDagsterType = create_any_type(name="SomeType", materializer=return_int)

    @lambda_solid(output_def=OutputDefinition(SomeDagsterType))
    def return_one():
        return 1

    pipeline_def = PipelineDefinition(name="single_int_output_pipeline", solid_defs=[return_one])

    with pytest.raises(
        DagsterInvariantViolationError, match="You must return an AssetMaterialization"
    ):
        execute_pipeline(
            pipeline_def, run_config={"solids": {"return_one": {"outputs": [{"result": 2}]}}}
        )
