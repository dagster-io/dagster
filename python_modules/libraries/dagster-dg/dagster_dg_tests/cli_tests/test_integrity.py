import shutil
import subprocess

from dagster_dg.cli import cli
from dagster_dg.utils import DgClickCommand, DgClickGroup

from dagster_dg_tests.utils import ProxyRunner, isolated_dg_venv


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


# Install dagster-dg in an isolated venv and make sure that it can execute. Without this test, it is
# easy to accidentally leave an import of a dependency present in the test environment inside
# dagster-dg, which causes the executable to fail when it is installed from pypi without those test
# dependencies.
def test_isolated_dg_executes():
    with ProxyRunner.test() as runner, isolated_dg_venv(runner) as venv_path:
        dg_path = shutil.which("dg")
        assert dg_path is not None, "dg executable not found in PATH"
        assert dg_path.startswith(str(venv_path)), "dg executable not resolving to local venv"
        assert subprocess.check_output(["dg", "--help"])
