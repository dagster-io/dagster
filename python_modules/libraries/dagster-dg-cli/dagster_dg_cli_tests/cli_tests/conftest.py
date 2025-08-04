import pytest


@pytest.fixture(autouse=True)
def clear_defined_commands():
    """Reset the _commands_defined flag on scaffold_group between tests,
    to ensure the cache of scaffold subcommands is cleared. This isn't an issue outside
    of tests because we're not reusing a Python process between different dg venvs.
    """
    from dagster_dg_cli.cli.scaffold import scaffold_defs_group

    scaffold_defs_group._commands_defined = False  # noqa: SLF001
