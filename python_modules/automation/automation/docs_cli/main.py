"""Command-line interface for dagster-docs."""

import click

from automation.docs_cli.commands.check import check
from automation.docs_cli.commands.ls import ls
from automation.docs_cli.commands.watch import watch


@click.group()
def main():
    """Dagster documentation tools."""
    pass


main.add_command(ls)
main.add_command(check)
main.add_command(watch)


if __name__ == "__main__":
    main()
