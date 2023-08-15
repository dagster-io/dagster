from typing import Any, Mapping, Sequence

from dagster import (
    Output,
    _check as check,
)
from dagster._core.definitions import In, OpDefinition, op
from dagster._core.definitions.output import Out
from dagster._core.execution.context.compute import OpExecutionContext


def _compute_fn(
    context: OpExecutionContext, inputs: Mapping[str, Sequence[Mapping[str, object]]]
) -> Any:
    passed_rows = []
    seen = set()
    for row in inputs.values():
        for item in row:
            key = list(item.keys())[0]
            if key not in seen:
                seen.add(key)
                passed_rows.append(item)

    result = []
    result.extend(passed_rows)
    result.append({context.op.name: "compute_called"})
    yield Output(result)


def create_stub_op(name: str, value: object) -> OpDefinition:
    check.str_param(name, "name")

    @op(name=name)
    def _stub():
        return value

    return _stub


def create_root_op(name: str) -> OpDefinition:
    return OpDefinition(
        name=name,
        ins={f"{name}_input": In()},
        compute_fn=_compute_fn,
        outs={"result": Out()},
    )


def create_op_with_deps(name: str, *op_deps: OpDefinition):
    return OpDefinition(
        name=name,
        ins={dep.name: In() for dep in op_deps},
        compute_fn=_compute_fn,
        outs={"result": Out()},
    )


def input_set(name: str) -> Mapping[str, str]:
    return {name: "input_set"}
