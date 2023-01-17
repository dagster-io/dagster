from dagster import (
    Output,
    _check as check,
)
from dagster._core.definitions import In, InputDefinition, OpDefinition, lambda_solid
from dagster._core.definitions.output import Out


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
    result.append({context.solid.name: "compute_called"})
    yield Output(result)


def define_stub_solid(name, value):
    check.str_param(name, "name")

    @lambda_solid(name=name)
    def _stub():
        return value

    return _stub


def create_root_solid(name):
    input_name = name + "_input"
    inp = InputDefinition(input_name)

    return OpDefinition(
        name=name,
        ins={inp.name: In.from_definition(inp)},
        compute_fn=_compute_fn,
        outs={"result": Out()},
    )


def create_solid_with_deps(name, *solid_deps):
    inputs = [InputDefinition(solid_dep.name) for solid_dep in solid_deps]

    return OpDefinition(
        name=name,
        ins={input_def.name: In.from_definition(input_def) for input_def in inputs},
        compute_fn=_compute_fn,
        outs={"result": Out()},
    )


def input_set(name):
    return {name: "input_set"}
