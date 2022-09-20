from collections import defaultdict

from dagster import DependencyDefinition, GraphDefinition, In, Int, NodeInvocation, op
from dagster._legacy import (
    InputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    solid,
)


def test_aliased_solids():
    @op()
    def first():
        return ["first"]

    @op(ins={"prev": In()})
    def not_first(prev):
        return prev + ["not_first"]

    pipeline = GraphDefinition(
        node_defs=[first, not_first],
        name="test",
        dependencies={
            "not_first": {"prev": DependencyDefinition("first")},
            NodeInvocation("not_first", alias="second"): {
                "prev": DependencyDefinition("not_first")
            },
            NodeInvocation("not_first", alias="third"): {"prev": DependencyDefinition("second")},
        },
    ).to_job()

    result = pipeline.execute_in_process()
    assert result.success
    assert result.output_for_node("third") == [
        "first",
        "not_first",
        "not_first",
        "not_first",
    ]


def test_only_aliased_solids():
    @op()
    def first():
        return ["first"]

    @op(ins={"prev": In()})
    def not_first(prev):
        return prev + ["not_first"]

    pipeline = GraphDefinition(
        node_defs=[first, not_first],
        name="test",
        dependencies={
            NodeInvocation("first", alias="the_root"): {},
            NodeInvocation("not_first", alias="the_consequence"): {
                "prev": DependencyDefinition("the_root")
            },
        },
    ).to_job()

    result = pipeline.execute_in_process()
    assert result.success
    assert result.output_for_node("the_consequence") == ["first", "not_first"]


def test_aliased_configs():
    @op(ins={}, config_schema=Int)
    def load_constant(context):
        return context.op_config

    pipeline = GraphDefinition(
        node_defs=[load_constant],
        name="test",
        dependencies={
            NodeInvocation(load_constant.name, "load_a"): {},
            NodeInvocation(load_constant.name, "load_b"): {},
        },
    ).to_job()

    result = pipeline.execute_in_process(
        {"solids": {"load_a": {"config": 2}, "load_b": {"config": 3}}}
    )

    assert result.success
    assert result.output_for_node("load_a") == 2
    assert result.output_for_node("load_b") == 3


def test_aliased_solids_context():
    record = defaultdict(set)

    @op
    def log_things(context):
        solid_value = context.op.name
        solid_def_value = context.op_def.name
        record[solid_def_value].add(solid_value)

    pipeline = GraphDefinition(
        node_defs=[log_things],
        name="test",
        dependencies={
            NodeInvocation("log_things", "log_a"): {},
            NodeInvocation("log_things", "log_b"): {},
        },
    ).to_job()

    result = pipeline.execute_in_process()
    assert result.success

    assert dict(record) == {"log_things": set(["log_a", "log_b"])}
