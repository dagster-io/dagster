from dagster import In, OpDefinition, Out, Output
from dagster import _check as check
from dagster import op


def _compute_fn(context, inputs):
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


def define_stub_op(name, value):
    check.str_param(name, "name")

    @op(name=name)
    def _stub():
        return value

    return _stub


def create_root_op(name):

    return OpDefinition(
        name=name,
        ins={f"{name}_input": In()},
        outs=Out(),
        compute_fn=_compute_fn,
    )


def create_op_with_deps(name, *solid_deps):

    return OpDefinition(
        name=name,
        ins={solid_dep.name: In() for solid_dep in solid_deps},
        outs=Out(),
        compute_fn=_compute_fn,
    )


def input_set(name):
    return {name: "input_set"}
