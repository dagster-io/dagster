from dagster_dg.cli import cli
from dagster_dg.utils import DgClickCommand, DgClickGroup


# Important that all nodes of the command tree inherit from one of our customized click
# Command/Group subclasses to ensure that the help formatting is consistent.
def test_all_commands_custom_subclass():
    def crawl(command):
        assert isinstance(
            command, (DgClickGroup, DgClickCommand)
        ), f"Group is not a DgClickGroup or DgClickCommand: {command}"
        if isinstance(command, DgClickGroup):
            for command in command.commands.values():
                crawl(command)

    crawl(cli)


# Important that all nodes of the command tree inherit from one of our customized click
# Command/Group subclasses to ensure that the help formatting is consistent.
def test_all_commands_have_global_options():
    def crawl(command):
        assert isinstance(
            command, (DgClickGroup, DgClickCommand)
        ), f"Group is not a DgClickGroup or DgClickCommand: {command}"
        if isinstance(command, DgClickGroup):
            for command in command.commands.values():
                crawl(command)

    crawl(cli)
