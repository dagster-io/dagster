import click
from dagster_shared.cli.json import DagsterCliCommand, DagsterCliCommandInvocation, DagsterCliSchema
from dagster_shared.ipc import ipc_write_unary_response, read_unary_input

import dagster._check as check
from dagster._cli.asset import asset_materialize_command
from dagster._cli.definitions import definitions_validate_command
from dagster.components.cli.scaffold import scaffold_object_command


@click.group(name="json", hidden=True)
def json_cli() -> None:
    """[INTERNAL] These commands are intended to support internal use cases. Users should generally
    not invoke these commands interactively.
    """


@json_cli.command(
    name="call",
    help="[INTERNAL] This is an internal utility. Structured invocation of dagster commands from the dg cli.",
)
@click.option("--input-file", type=click.Path())
@click.option("--output-file", type=click.Path())
def json_command(input_file: str, output_file: str):
    invocation = read_unary_input(input_file, as_type=DagsterCliCommandInvocation)
    if invocation.name == ["dagster", "asset", "materialize"]:
        check.not_none(asset_materialize_command.callback)(
            **{
                "config": tuple(),
                "python_file": None,
                "module_name": None,
                "package_name": None,
                "working_directory": None,
                "attribute": None,
                **invocation.options,
            }
        )
    else:
        raise Exception(f"Unknown command: {invocation.name}")


@json_cli.command(
    name="schema",
    help="[INTERNAL] This is an internal utility. Structured invocation of dagster commands from the dg cli.",
)
@click.option("--output-file", type=click.Path())
def schema_command(output_file: str):
    schema = DagsterCliSchema(
        commands=[
            DagsterCliCommand(
                name=["dagster", "asset", "materialize"],
                options=[p.name for p in asset_materialize_command.params if p.name],
                capabilities=[],
            ),
            DagsterCliCommand(
                name=["dagster", "definitions", "validate"],
                options=[p.name for p in definitions_validate_command.params if p.name],
                capabilities=[],
            ),
            DagsterCliCommand(
                name=["dagster-components", "scaffold"],
                options=[p.name for p in scaffold_object_command.params if p.name],
                capabilities=[],
            ),
        ],
        capabilities=[],
    )

    ipc_write_unary_response(output_file, schema)
