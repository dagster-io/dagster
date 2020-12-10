from collections import defaultdict

import pytest
from dagster import (
    AssetMaterialization,
    DagsterInvalidDefinitionError,
    DagsterTypeCheckDidNotPass,
    DependencyDefinition,
    InputDefinition,
    Int,
    List,
    MultiDependencyDefinition,
    Nothing,
    Optional,
    Output,
    OutputDefinition,
    PipelineDefinition,
    SolidInvocation,
    execute_pipeline,
    lambda_solid,
    solid,
)
from dagster.core.execution.api import create_execution_plan


def _define_nothing_dep_pipeline():
    @lambda_solid(output_def=OutputDefinition(Nothing, "complete"))
    def start_nothing():
        pass

    @lambda_solid(
        input_defs=[
            InputDefinition("add_complete", Nothing),
            InputDefinition("yield_complete", Nothing),
        ]
    )
    def end_nothing():
        pass

    @lambda_solid(output_def=OutputDefinition(Int))
    def emit_value():
        return 1

    @lambda_solid(
        input_defs=[InputDefinition("on_complete", Nothing), InputDefinition("num", Int)],
        output_def=OutputDefinition(Int),
    )
    def add_value(num):
        return 1 + num

    @solid(
        name="yield_values",
        input_defs=[InputDefinition("on_complete", Nothing)],
        output_defs=[
            OutputDefinition(Int, "num_1"),
            OutputDefinition(Int, "num_2"),
            OutputDefinition(Nothing, "complete"),
        ],
    )
    def yield_values(_context):
        yield Output(1, "num_1")
        yield Output(2, "num_2")
        yield Output(None, "complete")

    return PipelineDefinition(
        name="simple_exc",
        solid_defs=[emit_value, add_value, start_nothing, end_nothing, yield_values],
        dependencies={
            "add_value": {
                "on_complete": DependencyDefinition("start_nothing", "complete"),
                "num": DependencyDefinition("emit_value"),
            },
            "yield_values": {"on_complete": DependencyDefinition("start_nothing", "complete")},
            "end_nothing": {
                "add_complete": DependencyDefinition("add_value"),
                "yield_complete": DependencyDefinition("yield_values", "complete"),
            },
        },
    )


def test_valid_nothing_dependencies():

    result = execute_pipeline(_define_nothing_dep_pipeline())

    assert result.success


def test_invalid_input_dependency():
    @lambda_solid(output_def=OutputDefinition(Nothing))
    def do_nothing():
        pass

    @lambda_solid(input_defs=[InputDefinition("num", Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    with pytest.raises(DagsterInvalidDefinitionError):
        PipelineDefinition(
            name="bad_dep",
            solid_defs=[do_nothing, add_one],
            dependencies={"add_one": {"num": DependencyDefinition("do_nothing")}},
        )


def test_result_type_check():
    @solid(output_defs=[OutputDefinition(Nothing)])
    def bad(_context):
        yield Output("oops")

    pipeline = PipelineDefinition(name="fail", solid_defs=[bad])
    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(pipeline)


def test_nothing_inputs():
    @lambda_solid(input_defs=[InputDefinition("never_defined", Nothing)])
    def emit_one():
        return 1

    @lambda_solid
    def emit_two():
        return 2

    @lambda_solid
    def emit_three():
        return 3

    @lambda_solid(output_def=OutputDefinition(Nothing))
    def emit_nothing():
        pass

    @solid(
        input_defs=[
            InputDefinition("_one", Nothing),
            InputDefinition("one", Int),
            InputDefinition("_two", Nothing),
            InputDefinition("two", Int),
            InputDefinition("_three", Nothing),
            InputDefinition("three", Int),
        ]
    )
    def adder(_context, one, two, three):
        assert one == 1
        assert two == 2
        assert three == 3
        return one + two + three

    pipeline = PipelineDefinition(
        name="input_test",
        solid_defs=[emit_one, emit_two, emit_three, emit_nothing, adder],
        dependencies={
            SolidInvocation("emit_nothing", "_one"): {},
            SolidInvocation("emit_nothing", "_two"): {},
            SolidInvocation("emit_nothing", "_three"): {},
            "adder": {
                "_one": DependencyDefinition("_one"),
                "_two": DependencyDefinition("_two"),
                "_three": DependencyDefinition("_three"),
                "one": DependencyDefinition("emit_one"),
                "two": DependencyDefinition("emit_two"),
                "three": DependencyDefinition("emit_three"),
            },
        },
    )
    result = execute_pipeline(pipeline)
    assert result.success


def test_fanin_deps():
    called = defaultdict(int)

    @lambda_solid
    def emit_two():
        return 2

    @lambda_solid(output_def=OutputDefinition(Nothing))
    def emit_nothing():
        called["emit_nothing"] += 1

    @solid(
        input_defs=[
            InputDefinition("ready", Nothing),
            InputDefinition("num_1", Int),
            InputDefinition("num_2", Int),
        ]
    )
    def adder(_context, num_1, num_2):
        assert called["emit_nothing"] == 3
        called["adder"] += 1
        return num_1 + num_2

    pipeline = PipelineDefinition(
        name="input_test",
        solid_defs=[emit_two, emit_nothing, adder],
        dependencies={
            SolidInvocation("emit_two", "emit_1"): {},
            SolidInvocation("emit_two", "emit_2"): {},
            SolidInvocation("emit_nothing", "_one"): {},
            SolidInvocation("emit_nothing", "_two"): {},
            SolidInvocation("emit_nothing", "_three"): {},
            "adder": {
                "ready": MultiDependencyDefinition(
                    [
                        DependencyDefinition("_one"),
                        DependencyDefinition("_two"),
                        DependencyDefinition("_three"),
                    ]
                ),
                "num_1": DependencyDefinition("emit_1"),
                "num_2": DependencyDefinition("emit_2"),
            },
        },
    )
    result = execute_pipeline(pipeline)
    assert result.success
    assert called["adder"] == 1
    assert called["emit_nothing"] == 3


def test_valid_nothing_fns():
    @lambda_solid(output_def=OutputDefinition(Nothing))
    def just_pass():
        pass

    @solid(output_defs=[OutputDefinition(Nothing)])
    def just_pass2(_context):
        pass

    @lambda_solid(output_def=OutputDefinition(Nothing))
    def ret_none():
        return None

    @solid(output_defs=[OutputDefinition(Nothing)])
    def yield_none(_context):
        yield Output(None)

    @solid(output_defs=[OutputDefinition(Nothing)])
    def yield_stuff(_context):
        yield AssetMaterialization.file("/path/to/nowhere")

    pipeline = PipelineDefinition(
        name="fn_test", solid_defs=[just_pass, just_pass2, ret_none, yield_none, yield_stuff]
    )
    result = execute_pipeline(pipeline)
    assert result.success


def test_invalid_nothing_fns():
    @lambda_solid(output_def=OutputDefinition(Nothing))
    def ret_val():
        return "val"

    @solid(output_defs=[OutputDefinition(Nothing)])
    def yield_val(_context):
        yield Output("val")

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(PipelineDefinition(name="fn_test", solid_defs=[ret_val]))

    with pytest.raises(DagsterTypeCheckDidNotPass):
        execute_pipeline(PipelineDefinition(name="fn_test", solid_defs=[yield_val]))


def test_wrapping_nothing():
    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid(output_def=OutputDefinition(List[Nothing]))
        def _():
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid(input_defs=[InputDefinition("in", List[Nothing])])
        def _(_in):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid(output_def=OutputDefinition(Optional[Nothing]))
        def _():
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @lambda_solid(input_defs=[InputDefinition("in", Optional[Nothing])])
        def _(_in):
            pass


def test_execution_plan():
    @solid(output_defs=[OutputDefinition(Nothing)])
    def emit_nothing(_context):
        yield AssetMaterialization.file(path="/path/")

    @lambda_solid(input_defs=[InputDefinition("ready", Nothing)])
    def consume_nothing():
        pass

    pipe = PipelineDefinition(
        name="execution_plan_test",
        solid_defs=[emit_nothing, consume_nothing],
        dependencies={"consume_nothing": {"ready": DependencyDefinition("emit_nothing")}},
    )
    plan = create_execution_plan(pipe)

    levels = plan.get_steps_to_execute_by_level()

    assert "emit_nothing" in levels[0][0].key
    assert "consume_nothing" in levels[1][0].key

    assert execute_pipeline(pipe).success
