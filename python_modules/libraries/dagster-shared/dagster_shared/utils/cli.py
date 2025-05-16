import click


def command_to_schema(c: click.Command) -> dict:
    schema = {
        "name": c.name,
        "arguments": [_argument_to_schema(p) for p in c.params if isinstance(p, click.Argument)],
        "options": [_option_to_schema(p) for p in c.params if isinstance(p, click.Option)],
    }

    return schema


def schema_to_parameters(schema: dict) -> list[click.Parameter]:
    return [_schema_to_argument(p) for p in schema["arguments"]] + [
        _schema_to_option(p) for p in schema["options"]
    ]


def _argument_to_schema(p: click.Argument) -> dict:
    sch = _parameter_to_schema(p)
    sch["paramtype"] = "argument"
    return sch


def _option_to_schema(p: click.Option) -> dict:
    """Map a single Click option → a JSON‑Schema property."""
    sch = _parameter_to_schema(p)
    # defaults / descriptions ---------------------------------------------
    if p.default not in (None, ()):
        sch["default"] = p.default
    if p.help:
        sch["description"] = p.help

    sch["paramtype"] = "option"

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


def _schema_to_argument(schema: dict) -> click.Argument:
    """Convert a JSON schema dictionary back into a Click Argument object."""
    param_type = _schema_to_click_type(schema)
    return click.Argument([schema["name"]], type=param_type)


def _schema_to_option(schema: dict) -> click.Option:
    """Convert a JSON schema dictionary back into a Click Option object."""
    param_type = _schema_to_click_type(schema)

    # Build option flags
    flags = [f"--{schema['name'].replace('_', '-')}"]

    # Add help text if present
    help_text = schema.get("description")

    # Add default value if present
    default = schema.get("default")

    return click.Option(
        flags,
        type=param_type,
        help=help_text,
        default=default,
    )


def _schema_to_click_type(schema: dict) -> click.ParamType:
    """Convert a JSON schema type into a Click ParamType."""
    schema_type = schema.get("type")

    if schema_type == "integer":
        if "minimum" in schema or "maximum" in schema:
            return click.types.IntRange(min=schema.get("minimum"), max=schema.get("maximum"))
        return click.types.IntParamType()
    elif schema_type == "number":
        if "minimum" in schema or "maximum" in schema:
            return click.types.FloatRange(min=schema.get("minimum"), max=schema.get("maximum"))
        return click.types.FloatParamType()
    elif schema_type == "string":
        if "enum" in schema:
            return click.types.Choice(schema["enum"])
        elif schema.get("format") == "path":
            return click.types.Path()
        return click.types.StringParamType()
    elif schema_type == "boolean":
        return click.types.BoolParamType()
    else:
        raise Exception(f"Unsupported schema type: {schema_type}")
