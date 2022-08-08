import pytest

from dagster import (
    In,
    Out,
    op,
    Any,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Int,
    List,
    MultiDependencyDefinition,
    Nothing,
)
from dagster._core.definitions.composition import MappedInputPlaceholder
from dagster._core.definitions.solid_definition import CompositeSolidDefinition
from dagster._legacy import (
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    composite_solid,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)


def test_simple_values():
    @op(ins={"numbers": In(List[Int])})
    def sum_num(_context, numbers):
        # cant guarantee order
        assert set(numbers) == set([1, 2, 3])
        return sum(numbers)

    @op
    def emit_1():
        return 1

    @op
    def emit_2():
        return 2

    @op
    def emit_3():
        return 3

    result = execute_pipeline(
        PipelineDefinition(
            name="input_test",
            solid_defs=[emit_1, emit_2, emit_3, sum_num],
            dependencies={
                "sum_num": {
                    "numbers": MultiDependencyDefinition(
                        [
                            DependencyDefinition("emit_1"),
                            DependencyDefinition("emit_2"),
                            DependencyDefinition("emit_3"),
                        ]
                    )
                }
            },
        )
    )
    assert result.success
    assert result.result_for_solid("sum_num").output_value() == 6


@op(ins={"stuff": In(List[Any])})
def collect(_context, stuff):
    assert set(stuff) == set([1, None, "one"])
    return stuff


@op
def emit_num():
    return 1


@op
def emit_none():
    pass


@op
def emit_str():
    return "one"


@op(out=Out(Nothing))
def emit_nothing():
    pass


def test_interleaved_values():
    result = execute_pipeline(
        PipelineDefinition(
            name="input_test",
            solid_defs=[emit_num, emit_none, emit_str, collect],
            dependencies={
                "collect": {
                    "stuff": MultiDependencyDefinition(
                        [
                            DependencyDefinition("emit_num"),
                            DependencyDefinition("emit_none"),
                            DependencyDefinition("emit_str"),
                        ]
                    )
                }
            },
        )
    )
    assert result.success


def test_dsl():
    @pipeline
    def input_test():
        collect([emit_num(), emit_none(), emit_str()])

    result = execute_pipeline(input_test)

    assert result.success


def test_collect_one():
    @op
    def collect_one(list_arg):
        assert list_arg == ["one"]

    @pipeline
    def multi_one():
        collect_one([emit_str()])

    assert execute_pipeline(multi_one).success


def test_fan_in_manual():
    # manually building up this guy
    @composite_solid
    def _target_composite_dsl(str_in, none_in):
        num = emit_num()
        return collect([num, str_in, none_in])

    # base case works
    _target_composite_manual = CompositeSolidDefinition(
        name="manual_composite",
        solid_defs=[emit_num, collect],
        input_mappings=[
            InputDefinition("str_in").mapping_to("collect", "stuff", 1),
            InputDefinition("none_in").mapping_to("collect", "stuff", 2),
        ],
        output_mappings=[OutputDefinition().mapping_from("collect")],
        dependencies={
            "collect": {
                "stuff": MultiDependencyDefinition(
                    [
                        DependencyDefinition("emit_num"),
                        MappedInputPlaceholder,
                        MappedInputPlaceholder,
                    ]
                )
            }
        },
    )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="index 2 in the MultiDependencyDefinition is not a MappedInputPlaceholder",
    ):
        _missing_placeholder = CompositeSolidDefinition(
            name="manual_composite",
            solid_defs=[emit_num, collect],
            input_mappings=[
                InputDefinition("str_in").mapping_to("collect", "stuff", 1),
                InputDefinition("none_in").mapping_to("collect", "stuff", 2),
            ],
            output_mappings=[OutputDefinition().mapping_from("collect")],
            dependencies={
                "collect": {
                    "stuff": MultiDependencyDefinition(
                        [
                            DependencyDefinition("emit_num"),
                            MappedInputPlaceholder,
                        ]
                    )
                }
            },
        )

    with pytest.raises(
        DagsterInvalidDefinitionError, match="is not a MultiDependencyDefinition"
    ):
        _bad_target = CompositeSolidDefinition(
            name="manual_composite",
            solid_defs=[emit_num, collect],
            input_mappings=[
                InputDefinition("str_in").mapping_to("collect", "stuff", 1),
                InputDefinition("none_in").mapping_to("collect", "stuff", 2),
            ],
            output_mappings=[OutputDefinition().mapping_from("collect")],
            dependencies={"collect": {"stuff": DependencyDefinition("emit_num")}},
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Unsatisfied MappedInputPlaceholder at index 3",
    ):
        _missing_placeholder = CompositeSolidDefinition(
            name="manual_composite",
            solid_defs=[emit_num, collect],
            input_mappings=[
                InputDefinition("str_in").mapping_to("collect", "stuff", 1),
                InputDefinition("none_in").mapping_to("collect", "stuff", 2),
            ],
            output_mappings=[OutputDefinition().mapping_from("collect")],
            dependencies={
                "collect": {
                    "stuff": MultiDependencyDefinition(
                        [
                            DependencyDefinition("emit_num"),
                            MappedInputPlaceholder,
                            MappedInputPlaceholder,
                            MappedInputPlaceholder,
                        ]
                    )
                }
            },
        )


def test_nothing_deps():
    PipelineDefinition(
        name="input_test",
        solid_defs=[emit_num, emit_nothing, emit_str, collect],
        dependencies={
            "collect": {
                "stuff": MultiDependencyDefinition(
                    [
                        DependencyDefinition("emit_num"),
                        DependencyDefinition("emit_nothing"),
                        DependencyDefinition("emit_str"),
                    ]
                )
            }
        },
    )
