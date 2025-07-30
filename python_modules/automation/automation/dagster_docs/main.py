"""Unified command-line interface for Dagster documentation tools."""

import click

from automation.dagster_docs.commands.check import check
from automation.dagster_docs.commands.ls import ls
from automation.dagster_docs.commands.watch import watch


@click.group()
def main():
    """Dagster documentation tools."""
    pass


main.add_command(check)
main.add_command(ls)
main.add_command(watch)


if __name__ == "__main__":
    main()
