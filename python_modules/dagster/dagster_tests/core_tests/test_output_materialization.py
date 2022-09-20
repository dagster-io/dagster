import json

import pytest

from dagster import (
    AssetMaterialization,
    DagsterEventType,
    DagsterInvalidConfigError,
    GraphDefinition,
    In,
    Int,
    Out,
    Output,
    String,
    dagster_type_materializer,
    op,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.plan.step import StepKind
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.types.dagster_type import create_any_type
from dagster._legacy import InputDefinition, OutputDefinition, PipelineDefinition, execute_pipeline
from dagster._utils.test import get_temp_file_name, get_temp_file_names


def single_int_output_pipeline():
    @op(out=Out(Int))
    def return_one():
        return 1

    return GraphDefinition(name="single_int_output_pipeline", node_defs=[return_one]).to_job()


def single_string_output_pipeline():
    @op(out=Out(String))
    def return_foo():
        return "foo"

    return GraphDefinition(name="single_string_output_pipeline", node_defs=[return_foo]).to_job()


def multiple_output_pipeline():
    @op(
        out={
            "number": Out(
                Int,
            ),
            "string": Out(
                String,
            ),
        }
    )
    def return_one_and_foo(_context):
        yield Output(1, "number")
        yield Output("foo", "string")

    return GraphDefinition(name="multiple_output_pipeline", node_defs=[return_one_and_foo]).to_job()


def single_int_named_output_pipeline():
    @op(
        out={
            "named": Out(
                Int,
            )
        }
    )
    def return_named_one():
        return 1

    return GraphDefinition(
        name="single_int_named_output_pipeline", node_defs=[return_named_one]
    ).to_job()


def no_input_no_output_pipeline():
    @op(out={})
    def take_nothing_return_nothing(_context):
        pass

    return GraphDefinition(
        name="no_input_no_output_pipeline", node_defs=[take_nothing_return_nothing]
    ).to_job()


def one_input_no_output_pipeline():
    @op(ins={"dummy": In()}, out={})
    def take_input_return_nothing(_context, **_kwargs):
        pass

    return GraphDefinition(
        name="one_input_no_output_pipeline", node_defs=[take_input_return_nothing]
    ).to_job()


def test_basic_json_default_output_config_schema():
    env = ResolvedRunConfig.build(
        single_int_output_pipeline(),
        {"ops": {"return_one": {"outputs": [{"result": {"json": {"path": "foo"}}}]}}},
    )

    assert env.solids["return_one"]
    assert env.solids["return_one"].outputs.type_materializer_specs == [
        {"result": {"json": {"path": "foo"}}}
    ]


def test_basic_json_named_output_config_schema():
    env = ResolvedRunConfig.build(
        single_int_named_output_pipeline(),
        {"ops": {"return_named_one": {"outputs": [{"named": {"json": {"path": "foo"}}}]}}},
    )

    assert env.solids["return_named_one"]
    assert env.solids["return_named_one"].outputs.type_materializer_specs == [
        {"named": {"json": {"path": "foo"}}}
    ]


def test_basic_json_misnamed_output_config_schema():
    with pytest.raises(DagsterInvalidConfigError) as exc_context:
        ResolvedRunConfig.build(
            single_int_named_output_pipeline(),
            {"ops": {"return_named_one": {"outputs": [{"wrong_name": {"json": {"path": "foo"}}}]}}},
        )

    assert len(exc_context.value.errors) == 1
    assert 'Error 1: Received unexpected config entry "wrong_name"' in exc_context.value.message
    assert "at path root:ops:return_named_one:outputs[0]" in exc_context.value.message


def test_no_outputs_no_inputs_config_schema():
    assert ResolvedRunConfig.build(no_input_no_output_pipeline())

    with pytest.raises(DagsterInvalidConfigError) as exc_context:
        ResolvedRunConfig.build(no_input_no_output_pipeline(), {"ops": {"return_one": {}}})

    assert len(exc_context.value.errors) == 1
    assert (
        'Error 1: Received unexpected config entry "return_one" at path root:ops'
        in exc_context.value.message
    )


def test_no_outputs_one_input_config_schema():
    assert ResolvedRunConfig.build(
        one_input_no_output_pipeline(),
        {"ops": {"take_input_return_nothing": {"inputs": {"dummy": {"value": "value"}}}}},
    )

    with pytest.raises(DagsterInvalidConfigError) as exc_context:
        ResolvedRunConfig.build(
            one_input_no_output_pipeline(),
            {
                "ops": {
                    "take_input_return_nothing": {
                        "inputs": {"dummy": {"value": "value"}},
                        "outputs": {},
                    }
                }
            },
        )

    assert len(exc_context.value.errors) == 1
    exp_msg = 'Error 1: Received unexpected config entry "outputs" at path root:ops:take_input_return_nothing'
    assert exp_msg in exc_context.value.message


def test_basic_int_json_materialization():
    with get_temp_file_name() as filename:
        result = single_int_output_pipeline().execute_in_process(
            {"ops": {"return_one": {"outputs": [{"result": {"json": {"path": filename}}}]}}},
        )

        assert result.success

        with open(filename, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


def test_basic_materialization_event():
    with get_temp_file_name() as filename:
        result = single_int_output_pipeline().execute_in_process(
            {"ops": {"return_one": {"outputs": [{"result": {"json": {"path": filename}}}]}}},
        )

        assert result.success
        mat_event = result.filter_events(
            lambda evt: evt.step_key == "return_one" and evt.is_asset_materialization
        )[0]

        mat = mat_event.event_specific_data.materialization

        assert len(mat.metadata_entries) == 1
        assert mat.metadata_entries[0].path
        path = mat.metadata_entries[0].entry_data.path

        with open(path, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


def test_basic_string_json_materialization():
    pipeline = single_string_output_pipeline()

    with get_temp_file_name() as filename:
        result = pipeline.execute_in_process(
            {"ops": {"return_foo": {"outputs": [{"result": {"json": {"path": filename}}}]}}},
        )

        assert result.success

        with open(filename, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": "foo"}


def test_basic_int_and_string_json_materialization():

    pipeline = multiple_output_pipeline()

    with get_temp_file_names(2) as file_tuple:
        filename_one, filename_two = file_tuple  # pylint: disable=E0632
        result = pipeline.execute_in_process(
            {
                "ops": {
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

        with open(filename_one, "r", encoding="utf8") as ff_1:
            value = json.loads(ff_1.read())
            assert value == {"value": "foo"}

        with open(filename_two, "r", encoding="utf8") as ff_2:
            value = json.loads(ff_2.read())
            assert value == {"value": 1}


def read_file_contents(path):
    with open(path, "r", encoding="utf8") as ff:
        return ff.read()


def test_basic_int_and_string_json_multiple_materialization():

    pipeline = multiple_output_pipeline()

    with get_temp_file_names(4) as file_tuple:
        # False positive for unbalanced tuple unpacking
        # pylint: disable=E0632
        filename_one, filename_two, filename_three, filename_four = file_tuple
        result = pipeline.execute_in_process(
            {
                "ops": {
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

        with open(filename_one, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": "foo"}

        with open(filename_two, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": "foo"}

        with open(filename_three, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}

        with open(filename_four, "r", encoding="utf8") as ff:
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
        result = pipeline.execute_in_process(
            {
                "ops": {
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

        with open(filename_one, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}

        with open(filename_two, "r", encoding="utf8") as ff:
            value = json.loads(ff.read())
            assert value == {"value": 1}


@dagster_type_materializer(Int)
def yield_two_materializations(*_args, **_kwargs):
    yield AssetMaterialization("first")
    yield AssetMaterialization("second")


def test_basic_yield_multiple_materializations():
    SomeDagsterType = create_any_type(name="SomeType", materializer=yield_two_materializations)

    @op(out=Out(SomeDagsterType))
    def return_one():
        return 1

    pipeline_def = GraphDefinition(
        name="single_int_output_pipeline", node_defs=[return_one]
    ).to_job()
    result = pipeline_def.execute_in_process(
        run_config={"ops": {"return_one": {"outputs": [{"result": 2}]}}},
    )
    assert result.success

    assert len(result.filter_events(lambda evt: evt.is_asset_materialization)) == 2


@dagster_type_materializer(Int)
def return_int(*_args, **_kwargs):
    return 1


def test_basic_bad_output_materialization():
    SomeDagsterType = create_any_type(name="SomeType", materializer=return_int)

    @op(out=Out(SomeDagsterType))
    def return_one():
        return 1

    pipeline_def = GraphDefinition(
        name="single_int_output_pipeline", node_defs=[return_one]
    ).to_job()

    with pytest.raises(
        DagsterInvariantViolationError, match="You must return an AssetMaterialization"
    ):
        pipeline_def.execute_in_process(
            run_config={"ops": {"return_one": {"outputs": [{"result": 2}]}}},
        )
