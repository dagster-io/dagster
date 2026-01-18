from collections import defaultdict

import dagster as dg
from dagster import Int


def test_aliased_ops():
    @dg.op()
    def first():
        return ["first"]

    @dg.op(ins={"prev": dg.In()})
    def not_first(prev):
        return prev + ["not_first"]

    job_def = dg.GraphDefinition(
        node_defs=[first, not_first],
        name="test",
        dependencies={  # pyright: ignore[reportArgumentType]
            "not_first": {"prev": dg.DependencyDefinition("first")},
            dg.NodeInvocation("not_first", alias="second"): {
                "prev": dg.DependencyDefinition("not_first")
            },
            dg.NodeInvocation("not_first", alias="third"): {
                "prev": dg.DependencyDefinition("second")
            },
        },
    ).to_job()

    result = job_def.execute_in_process()
    assert result.success
    assert result.output_for_node("third") == [
        "first",
        "not_first",
        "not_first",
        "not_first",
    ]


def test_only_aliased_ops():
    @dg.op()
    def first():
        return ["first"]

    @dg.op(ins={"prev": dg.In()})
    def not_first(prev):
        return prev + ["not_first"]

    job_def = dg.GraphDefinition(
        node_defs=[first, not_first],
        name="test",
        dependencies={
            dg.NodeInvocation("first", alias="the_root"): {},
            dg.NodeInvocation("not_first", alias="the_consequence"): {
                "prev": dg.DependencyDefinition("the_root")
            },
        },
    ).to_job()

    result = job_def.execute_in_process()
    assert result.success
    assert result.output_for_node("the_consequence") == ["first", "not_first"]


def test_aliased_configs():
    @dg.op(ins={}, config_schema=Int)
    def load_constant(context):
        return context.op_config

    job_def = dg.GraphDefinition(
        node_defs=[load_constant],
        name="test",
        dependencies={
            dg.NodeInvocation(load_constant.name, "load_a"): {},
            dg.NodeInvocation(load_constant.name, "load_b"): {},
        },
    ).to_job()

    result = job_def.execute_in_process({"ops": {"load_a": {"config": 2}, "load_b": {"config": 3}}})

    assert result.success
    assert result.output_for_node("load_a") == 2
    assert result.output_for_node("load_b") == 3


def test_aliased_ops_context():
    record = defaultdict(set)

    @dg.op
    def log_things(context):
        op_value = context.op.name
        op_def_value = context.op_def.name
        record[op_def_value].add(op_value)

    job_def = dg.GraphDefinition(
        node_defs=[log_things],
        name="test",
        dependencies={
            dg.NodeInvocation("log_things", "log_a"): {},
            dg.NodeInvocation("log_things", "log_b"): {},
        },
    ).to_job()

    result = job_def.execute_in_process()
    assert result.success

    assert dict(record) == {"log_things": set(["log_a", "log_b"])}
