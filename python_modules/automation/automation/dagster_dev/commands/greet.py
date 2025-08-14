"""Example command for dagster-dev CLI."""

import click


@click.command()
@click.argument("name", type=str)
@click.option("--greeting", "-g", default="Hello", help="Greeting to use")
@click.option("--uppercase", "-u", is_flag=True, help="Convert output to uppercase")
def greet(name, greeting, uppercase):
    """Greet someone with a customizable message.

    This is an example command that demonstrates how to create commands
    for the dagster-dev CLI. Commands are automatically discovered and
    added to the CLI.

    NAME is the person to greet.
    """
    message = f"{greeting}, {name}!"

    if uppercase:
        message = message.upper()

    click.echo(message)
