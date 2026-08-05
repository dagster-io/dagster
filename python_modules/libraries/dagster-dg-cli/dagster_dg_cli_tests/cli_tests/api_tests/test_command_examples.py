"""Mitigation test: every leaf `dg api` command must include an Example block in its docstring.

The Example block is what makes the auto-generated reference page (and the `--help`
output) show users what the command actually returns. If a new `dg api` command lands
without one, this test fails with a pointer to the missing command.
"""

import click
import pytest
from dagster_dg_cli.cli.api.cli_group import api_group


def _iter_leaf_commands(
    group: click.Group, prefix: tuple[str, ...]
) -> list[tuple[str, click.Command]]:
    leaves: list[tuple[str, click.Command]] = []
    for name, cmd in group.commands.items():
        path = (*prefix, name)
        if isinstance(cmd, click.Group):
            leaves.extend(_iter_leaf_commands(cmd, path))
        else:
            leaves.append((" ".join(path), cmd))
    return leaves


_LEAF_COMMANDS: list[tuple[str, click.Command]] = _iter_leaf_commands(api_group, ("dg", "api"))


@pytest.mark.parametrize(
    ("command_path", "command"),
    _LEAF_COMMANDS,
    ids=[path for path, _ in _LEAF_COMMANDS],
)
def test_dg_api_command_has_example_in_docstring(command_path: str, command: click.Command) -> None:
    """Every leaf `dg api` command must surface an Example: block in its docstring.

    The auto-generated reference page (`docs/docs/api/clis/dg-cli/dg-api.mdx`) renders
    these Example blocks inline so users can see what each command returns without
    making a test call.
    """
    doc = command.help or ""
    assert "Example:" in doc, (
        f"`{command_path}` is missing an `Example:` block in its docstring. "
        f"Add one so users can see what the command returns. "
        f"See dagster_dg_cli/cli/api/secret.py for the format to follow."
    )
