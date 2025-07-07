import dagster as dg
import pytest
from dagster._core.definitions.composition import MappedInputPlaceholder


def test_simple_values():
    @dg.op(ins={"numbers": dg.In(dg.List[dg.Int])})
    def sum_num(_context, numbers):
        # cant guarantee order
        assert set(numbers) == set([1, 2, 3])
        return sum(numbers)

    @dg.op
    def emit_1():
        return 1

    @dg.op
    def emit_2():
        return 2

    @dg.op
    def emit_3():
        return 3

    foo_job = dg.GraphDefinition(
        name="input_test",
        node_defs=[emit_1, emit_2, emit_3, sum_num],
        dependencies={
            "sum_num": {
                "numbers": dg.MultiDependencyDefinition(
                    [
                        dg.DependencyDefinition("emit_1"),
                        dg.DependencyDefinition("emit_2"),
                        dg.DependencyDefinition("emit_3"),
                    ]
                )
            }
        },
    ).to_job()
    result = foo_job.execute_in_process()
    assert result.success
    assert result.output_for_node("sum_num") == 6


@dg.op(ins={"stuff": dg.In(dg.List[dg.Any])})
def collect(_context, stuff):
    assert set(stuff) == set([1, None, "one"])
    return stuff


@dg.op
def emit_num():
    return 1


@dg.op
def emit_none():
    pass


@dg.op
def emit_str():
    return "one"


@dg.op(out=dg.Out(dg.Nothing))
def emit_nothing():
    pass


def test_interleaved_values():
    foo_job = dg.GraphDefinition(
        name="input_test",
        node_defs=[emit_num, emit_none, emit_str, collect],
        dependencies={
            "collect": {
                "stuff": dg.MultiDependencyDefinition(
                    [
                        dg.DependencyDefinition("emit_num"),
                        dg.DependencyDefinition("emit_none"),
                        dg.DependencyDefinition("emit_str"),
                    ]
                )
            }
        },
    ).to_job()
    result = foo_job.execute_in_process()
    assert result.success


def test_dsl():
    @dg.job
    def input_test():
        collect([emit_num(), emit_none(), emit_str()])

    result = input_test.execute_in_process()

    assert result.success


def test_collect_one():
    @dg.op
    def collect_one(list_arg):
        assert list_arg == ["one"]

    @dg.job
    def multi_one():
        collect_one([emit_str()])

    assert multi_one.execute_in_process().success


def test_fan_in_manual():
    # manually building up this guy
    @dg.graph
    def _target_graph_dsl(str_in, none_in):
        num = emit_num()
        return collect([num, str_in, none_in])

    # base case works
    _target_graph_manual = dg.GraphDefinition(
        name="manual_graph",
        node_defs=[emit_num, collect],
        input_mappings=[
            dg.InputMapping(
                graph_input_name="str_in",
                mapped_node_name="collect",
                mapped_node_input_name="stuff",
                fan_in_index=1,
            ),
            dg.InputMapping(
                graph_input_name="none_in",
                mapped_node_name="collect",
                mapped_node_input_name="stuff",
                fan_in_index=2,
            ),
        ],
        output_mappings=[
            dg.OutputMapping(
                graph_output_name="result",
                mapped_node_name="collect",
                mapped_node_output_name="result",
            )
        ],
        dependencies={
            "collect": {
                "stuff": dg.MultiDependencyDefinition(
                    [
                        dg.DependencyDefinition("emit_num"),
                        MappedInputPlaceholder,
                        MappedInputPlaceholder,
                    ]
                )
            }
        },
    )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="index 2 in the MultiDependencyDefinition is not a MappedInputPlaceholder",
    ):
        _missing_placeholder = dg.GraphDefinition(
            name="manual_graph",
            node_defs=[emit_num, collect],
            input_mappings=[
                dg.InputMapping(
                    graph_input_name="str_in",
                    mapped_node_name="collect",
                    mapped_node_input_name="stuff",
                    fan_in_index=1,
                ),
                dg.InputMapping(
                    graph_input_name="none_in",
                    mapped_node_name="collect",
                    mapped_node_input_name="stuff",
                    fan_in_index=2,
                ),
            ],
            output_mappings=[
                dg.OutputMapping(
                    graph_output_name="result",
                    mapped_node_name="collect",
                    mapped_node_output_name="result",
                )
            ],
            dependencies={
                "collect": {
                    "stuff": dg.MultiDependencyDefinition(
                        [
                            dg.DependencyDefinition("emit_num"),
                            MappedInputPlaceholder,
                        ]
                    )
                }
            },
        )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError, match="is not a MultiDependencyDefinition"
    ):
        _bad_target = dg.GraphDefinition(
            name="manual_graph",
            node_defs=[emit_num, collect],
            input_mappings=[
                dg.InputMapping(
                    graph_input_name="str_in",
                    mapped_node_name="collect",
                    mapped_node_input_name="stuff",
                    fan_in_index=1,
                ),
                dg.InputMapping(
                    graph_input_name="none_in",
                    mapped_node_name="collect",
                    mapped_node_input_name="stuff",
                    fan_in_index=2,
                ),
            ],
            output_mappings=[
                dg.OutputMapping(
                    graph_output_name="result",
                    mapped_node_name="collect",
                    mapped_node_output_name="result",
                )
            ],
            dependencies={"collect": {"stuff": dg.DependencyDefinition("emit_num")}},
        )

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="Unsatisfied MappedInputPlaceholder at index 3",
    ):
        _missing_placeholder = dg.GraphDefinition(
            name="manual_graph",
            node_defs=[emit_num, collect],
            input_mappings=[
                dg.InputMapping(
                    graph_input_name="str_in",
                    mapped_node_name="collect",
                    mapped_node_input_name="stuff",
                    fan_in_index=1,
                ),
                dg.InputMapping(
                    graph_input_name="none_in",
                    mapped_node_name="collect",
                    mapped_node_input_name="stuff",
                    fan_in_index=2,
                ),
            ],
            output_mappings=[
                dg.OutputMapping(
                    graph_output_name="result",
                    mapped_node_name="collect",
                    mapped_node_output_name="result",
                )
            ],
            dependencies={
                "collect": {
                    "stuff": dg.MultiDependencyDefinition(
                        [
                            dg.DependencyDefinition("emit_num"),
                            MappedInputPlaceholder,
                            MappedInputPlaceholder,
                            MappedInputPlaceholder,
                        ]
                    )
                }
            },
        )


def test_nothing_deps():
    dg.GraphDefinition(
        name="input_test",
        node_defs=[emit_num, emit_nothing, emit_str, collect],
        dependencies={
            "collect": {
                "stuff": dg.MultiDependencyDefinition(
                    [
                        dg.DependencyDefinition("emit_num"),
                        dg.DependencyDefinition("emit_nothing"),
                        dg.DependencyDefinition("emit_str"),
                    ]
                )
            }
        },
    ).to_job()
