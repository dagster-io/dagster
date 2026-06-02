from dagster_cloud_cli.entrypoint import app
from typer import Typer
from typer.models import CommandInfo, TyperInfo


def _gather_groups_and_commands(t: Typer) -> tuple[list[TyperInfo], list[CommandInfo]]:
    groups = t.registered_groups
    commands = t.registered_commands

    for subgroup in t.registered_groups:
        if subgroup.typer_instance:
            sg_groups, sg_commands = _gather_groups_and_commands(subgroup.typer_instance)
            groups.extend(sg_groups)
            commands.extend(sg_commands)

    return groups, commands


def _group_has_help(info: TyperInfo):
    instance_has_help = info.typer_instance and _group_has_help(info.typer_instance.info)
    return info.help or info.short_help or info.hidden or instance_has_help


def _command_has_help(info: CommandInfo):
    return info.help or info.short_help or info.hidden or (info.callback and info.callback.__doc__)


def test_all_commands_and_groups_have_help_text():
    """Validates that all Typer commands and command groups have help text defined."""
    groups, commands = _gather_groups_and_commands(app)

    for group in groups:
        assert _group_has_help(group), f"Group {group.name} has no helptext"
    for command in commands:
        assert _command_has_help(command), f"Command {command.name} has no helptext"
