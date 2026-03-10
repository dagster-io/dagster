import importlib
import json

import click


def dg_response_schema(*, module: str, cls: str):
    """Add a --response-schema flag to a Click command.

    When --response-schema is passed, lazily imports the Pydantic model from
    ``module`` and prints its JSON Schema, then exits. The import is deferred
    so it only happens when the flag is actually used.

    Args:
        module: Fully-qualified module path (e.g. "dagster_dg_cli.cli.schemas.list_schemas").
        cls: Class name within that module (e.g. "DgComponentList").
    """

    def callback(ctx, param, value):
        if not value:
            return
        mod = importlib.import_module(module)
        model_cls = getattr(mod, cls)
        click.echo(json.dumps(model_cls.model_json_schema(), indent=2))
        ctx.exit(0)

    def decorator(func):
        return click.option(
            "--response-schema",
            is_flag=True,
            is_eager=True,
            expose_value=False,
            help="Print the JSON Schema of the response model and exit.",
            callback=callback,
        )(func)

    return decorator
