from dagster import Output
from dagster import _check as check
from dagster._core.definitions import (
    InputDefinition,
    OutputDefinition,
    SolidDefinition,
    lambda_solid,
)


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

    return SolidDefinition(
        name=name,
        input_defs=[inp],
        compute_fn=_compute_fn,
        output_defs=[OutputDefinition()],
    )


def create_solid_with_deps(name, *solid_deps):
    inputs = [InputDefinition(solid_dep.name) for solid_dep in solid_deps]

    return SolidDefinition(
        name=name,
        input_defs=inputs,
        compute_fn=_compute_fn,
        output_defs=[OutputDefinition()],
    )


def input_set(name):
    return {name: "input_set"}
