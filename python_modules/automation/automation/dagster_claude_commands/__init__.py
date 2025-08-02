"""Dagster Claude Commands - Automated workflows for development."""

import click


@click.group()
def main():
    """Dagster Claude Commands - Automated workflows for development."""
    pass


# Import and register commands
from automation.dagster_claude_commands.commands.submit_summarized_pr_group import (
    submit_summarized_pr,
)

main.add_command(submit_summarized_pr)


if __name__ == "__main__":
    main()
