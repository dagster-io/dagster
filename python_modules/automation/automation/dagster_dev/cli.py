"""Main CLI entry point for dagster-dev commands."""

import importlib
import inspect
import pkgutil

import click

from automation.dagster_dev import commands


def discover_commands():
    """Discover and load all commands from the commands directory.

    Returns:
        dict: Mapping of command name to click command function
    """
    discovered_commands = {}

    # Iterate through all Python files in the commands directory
    for module_info in pkgutil.iter_modules(commands.__path__, commands.__name__ + "."):
        if module_info.name.endswith(".__init__"):
            continue

        # Import the module
        module = importlib.import_module(module_info.name)

        # Look for click commands in the module
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, click.Command):
                # Use the command name from click, or fallback to module name
                cmd_name = obj.name or module_info.name.split(".")[-1]
                discovered_commands[cmd_name] = obj

    return discovered_commands


@click.group()
@click.version_option()
def cli():
    """Dagster developer utilities CLI.

    A collection of commands to streamline development workflows within the Dagster repository.
    Commands are auto-discovered from the commands/ directory.
    """
    pass


def create_list_command(discovered_commands):
    """Create a dynamic list command that shows all available commands."""

    @click.command(name="list")
    def list_commands():
        """List all available dagster-dev commands with descriptions for agent consumption."""
        click.echo("Available dagster-dev commands:\n")

        for cmd_name, cmd_obj in sorted(discovered_commands.items()):
            # Get the short description from the command docstring
            description = "No description available"
            if cmd_obj.help:
                description = cmd_obj.help.split("\n")[0].strip()
            elif cmd_obj.short_help:
                description = cmd_obj.short_help

            click.echo(f"  {cmd_name:<20} {description}")

            # Show parameters/options for agent consumption
            if cmd_obj.params:
                for param in cmd_obj.params:
                    if isinstance(param, click.Option):
                        opts = "/".join(param.opts)
                        param_help = param.help or "No help available"
                        click.echo(f"    {opts:<18} {param_help}")
                    elif isinstance(param, click.Argument):
                        param_help = f"Argument: {param.name}"
                        click.echo(f"    {param.name:<18} {param_help}")

        click.echo(f"\nTotal commands: {len(discovered_commands)}")
        click.echo("\nUse 'dagster-dev <command> --help' for detailed help on any command.")

    return list_commands


def main():
    """Main entry point for the dagster-dev CLI."""
    # Discover all available commands
    discovered_commands = discover_commands()

    # Add discovered commands to the CLI group
    for cmd_name, cmd_obj in discovered_commands.items():
        cli.add_command(cmd_obj, name=cmd_name)

    # Add the list command
    list_cmd = create_list_command(discovered_commands)
    cli.add_command(list_cmd)

    # Run the CLI
    cli()


if __name__ == "__main__":
    main()
