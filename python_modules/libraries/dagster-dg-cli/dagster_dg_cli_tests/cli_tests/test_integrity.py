import ast
import pathlib
import shutil
import subprocess

import dagster_dg_cli
from dagster_dg_cli.cli import cli
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_test.dg_utils.utils import ProxyRunner, isolated_dg_venv

_REQUESTS_HTTP_VERBS = {"get", "post", "put", "delete", "patch", "head", "request"}


# Important that all nodes of the command tree inherit from one of our customized click
# Command/Group subclasses to ensure that the help formatting is consistent.
def test_all_commands_custom_subclass():
    def crawl(command):
        assert isinstance(command, (DgClickGroup, DgClickCommand)), (
            f"Group is not a DgClickGroup or DgClickCommand: {command}"
        )
        if isinstance(command, DgClickGroup):
            for command in command.commands.values():
                crawl(command)

    crawl(cli)


# Important that all nodes of the command tree inherit from one of our customized click
# Command/Group subclasses to ensure that the help formatting is consistent.
def test_all_commands_have_global_options():
    def crawl(command):
        assert isinstance(command, (DgClickGroup, DgClickCommand)), (
            f"Group is not a DgClickGroup or DgClickCommand: {command}"
        )
        if isinstance(command, DgClickGroup):
            for command in command.commands.values():
                crawl(command)

    crawl(cli)


# Install dagster-dg-cli in an isolated venv and make sure that it can execute. Without this test, it is
# easy to accidentally leave an import of a dependency present in the test environment inside
# dagster-dg-cli, which causes the executable to fail when it is installed from pypi without those test
# dependencies.
def test_isolated_dg_executes():
    with ProxyRunner.test() as runner, isolated_dg_venv(runner) as venv_path:
        dg_path = shutil.which("dg")
        assert dg_path is not None, "dg executable not found in PATH"
        assert dg_path.startswith(str(venv_path)), "dg executable not resolving to local venv"
        assert subprocess.check_output(["dg", "--help"])


def _iter_requests_calls_without_timeout(tree: ast.AST):
    """Yield ast.Call nodes that look like ``requests.<verb>(...)`` and have
    no ``timeout=`` keyword argument. Picks up both bare ``requests.get(...)``
    and aliased ``r.get(...)`` where the receiver is named ``requests`` (the
    common pattern in this package).
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr not in _REQUESTS_HTTP_VERBS:
            continue
        # `requests.<verb>(...)` — receiver must be a Name whose id is "requests"
        if not isinstance(func.value, ast.Name) or func.value.id != "requests":
            continue
        if any(kw.arg == "timeout" for kw in node.keywords):
            continue
        yield node


def test_all_requests_calls_have_timeout():
    """Regression guard for #33747.

    The default for ``requests.<verb>(...)`` is no timeout, which means a
    misconfigured URL or unreachable Plus instance hangs the CLI forever.
    Every direct ``requests`` call inside ``dagster_dg_cli`` must pass
    ``timeout=...`` explicitly.
    """
    pkg_root = pathlib.Path(dagster_dg_cli.__file__).parent
    offenders: list[str] = []
    for path in pkg_root.rglob("*.py"):
        # Skip vendored / test data; we only want the shipped CLI sources.
        if any(part.endswith("_tests") or part == "tests" for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - shouldn't happen
            continue
        for call in _iter_requests_calls_without_timeout(tree):
            offenders.append(f"{path.relative_to(pkg_root.parent)}:{call.lineno}")

    assert offenders == [], (
        "requests.* calls without an explicit `timeout=` kwarg "
        "(see #33747 — the CLI hangs forever otherwise):\n  " + "\n  ".join(offenders)
    )
