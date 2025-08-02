"""Dagster Claude Commands - Automated workflows for development."""

import click


@click.group()
def main():
    """Dagster Claude Commands - Automated workflows for development."""
    pass


# Commands will be imported and registered here as they are added
# Example:
# from automation.dagster_claude_commands.commands.example import example_command
# main.add_command(example_command)


if __name__ == "__main__":
    main()
