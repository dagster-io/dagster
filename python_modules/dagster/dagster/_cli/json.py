import json

import click

from dagster._cli.asset import asset_materialize_command


@click.command(name="json")
def json_command():
    """Commands for working with Dagster JSON."""
    schema = [
        (["asset", "materialize"], _command_to_schema(asset_materialize_command)),
    ]

    # Use output file instead

    print(json.dumps(schema))


def _command_to_schema(c: click.Command) -> dict:
    schema = {
        "name": c.name,
        "arguments": [_argument_to_schema(p) for p in c.params if isinstance(p, click.Argument)],
        "options": [_option_to_schema(p) for p in c.params if isinstance(p, click.Option)],
    }

    return schema


def _argument_to_schema(p: click.Argument) -> dict:
    return _parameter_to_schema(p)


def _option_to_schema(p: click.Option) -> dict:
    """Map a single Click option → a JSON‑Schema property."""
    sch = _parameter_to_schema(p)
    # defaults / descriptions ---------------------------------------------
    if p.default not in (None, ()):
        sch["default"] = p.default
    if p.help:
        sch["description"] = p.help
    return sch


def _parameter_to_schema(p: click.Parameter) -> dict:
    """Map a single Click argument → a JSON‑Schema property."""
    sch: dict = {
        "name": p.name,
    }

    # ---- map the Click type → JSON‑Schema type ---------------------------
    if isinstance(p.type, click.types.IntParamType):
        sch["type"] = "integer"
    elif isinstance(p.type, click.types.IntRange):
        sch["type"] = "integer"
        if p.type.min is not None:
            sch["minimum"] = p.type.min
        if p.type.max is not None:
            sch["maximum"] = p.type.max
    elif isinstance(p.type, click.types.FloatRange):
        sch["type"] = "number"
    elif isinstance(p.type, click.types.Path):
        sch["type"] = "string"
        sch["format"] = "path"
    elif isinstance(p.type, click.types.Choice):
        sch["type"] = "string"
        sch["enum"] = list(p.type.choices)
    elif isinstance(p.type, click.types.BoolParamType):
        sch["type"] = "boolean"
    elif isinstance(p.type, click.types.StringParamType):
        sch["type"] = "string"
    else:  # fallback
        raise Exception(f"Unsupported type: {type(p.type)}")

    return sch
