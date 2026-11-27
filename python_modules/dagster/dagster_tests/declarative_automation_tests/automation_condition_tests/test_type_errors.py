"""Type-level tests for the automation condition APIs.

The test asserts that:

  1. every annotated line produces an error matching the regex for that checker, and
  2. no other line produces any error at all (so the positive cases double as
     assertions that valid usage typechecks cleanly).

Two checkers run as separate parametrizations, each skipping if unavailable:

  - `ty`: the internal repo's standard checker; installed in the workspace venv
    (dev dependency of the repo root), absent from tox envs.
  - `pyright`: installed in every dagster tox env, but only able to resolve the
    editable dagster install under the `type_signature_tests` tox env (compat-mode
    install); elsewhere the test detects the unresolved import and skips.

Like the other `typesignature` tests, this is deselected by default (see conftest.py);
run it explicitly with `pytest <this file> -m typesignature`.
"""

import json
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

_CASES_PATH = Path(__file__).parent / "automation_condition_type_error_cases.py"

# strips the trailing markers that hide the deliberate errors from repo-wide checks
_TYPE_IGNORE_RE = re.compile(r"[ 	]*# type: ignore[ 	]*$", re.MULTILINE)


def _load_cases_source() -> str:
    """The cases live in a real module (see its docstring) whose deliberate errors are
    masked with `# type: ignore` markers; strip them so the checkers under test see
    the errors. Self-enforcing: an unstripped or superfluous marker surfaces as
    "expected an error, got none" / "unexpected error" below, and a missing marker
    fails the repo-wide type check instead.
    """
    source = _TYPE_IGNORE_RE.sub("", _CASES_PATH.read_text())
    assert source != _CASES_PATH.read_text(), "no markers stripped -- cases file is broken"
    return source


_ASSERTION_REGEX = re.compile(
    r"^\s*# assert-type-error-(?P<checker>ty|pyright): (?P<q>['\"])(?P<pattern>.+)(?P=q)\s*$"
)


def _expected_errors(snippet: str, checker: str) -> dict[int, str]:
    """Map line number -> expected error regex for the given checker.

    An `# assert-type-error-<checker>: '...'` comment applies to the next
    non-comment, non-blank line (so stacked comments for different checkers can
    annotate the same line).
    """
    expected: dict[int, str] = {}
    pending: str | None = None
    for lineno, line in enumerate(snippet.splitlines(), start=1):
        match = _ASSERTION_REGEX.match(line)
        if match:
            if match.group("checker") == checker:
                pending = match.group("pattern")
            continue
        if not line.strip() or line.strip().startswith("#"):
            continue
        if pending is not None:
            expected[lineno] = pending
            pending = None
    return expected


def _run_ty(snippet_path: Path) -> dict[int, list[str]]:
    result = subprocess.run(
        [
            "ty",
            "check",
            str(snippet_path),
            "--output-format=gitlab",
            # resolve `dagster` from the environment running this test
            "--python",
            sys.prefix,
        ],
        capture_output=True,
        text=True,
        cwd=snippet_path.parent,  # keep ty from discovering repo-level config
        check=False,
    )
    try:
        diagnostics = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"ty did not produce parseable output:\n{result.stdout}\n{result.stderr}"
        )
    errors: dict[int, list[str]] = defaultdict(list)
    for entry in diagnostics:
        errors[entry["location"]["positions"]["begin"]["line"]].append(entry["description"])
    return errors


def _run_pyright(snippet_path: Path) -> dict[int, list[str]]:
    result = subprocess.run(
        [
            "pyright",
            "--outputjson",
            "--pythonpath",
            sys.executable,
            str(snippet_path),
        ],
        capture_output=True,
        text=True,
        cwd=snippet_path.parent,
        check=False,
    )
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"pyright did not produce parseable output:\n{result.stdout}\n{result.stderr}"
        )
    errors: dict[int, list[str]] = defaultdict(list)
    for diag in output["generalDiagnostics"]:
        if diag["severity"] != "error":
            continue
        message = diag["message"]
        if 'Import "dagster" could not be resolved' in message:
            # pyright can only follow dagster's editable install under the
            # type_signature_tests tox env (compat-mode install) or a real install
            pytest.skip("pyright cannot resolve dagster in this environment")
        # pyright ranges are 0-based
        errors[diag["range"]["start"]["line"] + 1].append(message)
    return errors


_RUNNERS = {"ty": _run_ty, "pyright": _run_pyright}


@pytest.mark.typesignature
@pytest.mark.parametrize("checker", sorted(_RUNNERS))
def test_automation_condition_type_errors(checker: str, tmp_path: Path) -> None:
    if shutil.which(checker) is None:
        pytest.skip(f"{checker} is not installed in this environment")

    source = _load_cases_source()
    snippet_path = tmp_path / "automation_condition_snippet.py"
    snippet_path.write_text(source)

    expected = _expected_errors(source, checker)
    assert expected, "snippet contains no assertions for this checker -- test is broken"
    actual = _RUNNERS[checker](snippet_path)

    problems = []
    for lineno, pattern in expected.items():
        messages = actual.get(lineno, [])
        if not any(re.search(pattern, message) for message in messages):
            problems.append(
                f"line {lineno}: expected an error matching {pattern!r}, got: {messages or 'no errors'}"
            )
    for lineno, messages in sorted(actual.items()):
        if lineno not in expected:
            problems.append(f"line {lineno}: unexpected error(s): {messages}")

    assert not problems, f"{checker} mismatches:\n" + "\n".join(problems)


def _format_diagnostics() -> str:
    """Render the checkers' real diagnostics for the cases file.

    The `# type: ignore` markers in the cases file hide its deliberate errors from
    editors as well as from repo-wide type checks, so to inspect what the checkers
    actually report, run this file directly:

        python test_type_errors.py
    """
    import tempfile

    source = _load_cases_source()
    lines = source.splitlines()
    out: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        snippet_path = Path(tmp) / "automation_condition_snippet.py"
        snippet_path.write_text(source)
        for checker in sorted(_RUNNERS):
            out.append(f"――― {checker} " + "―" * 40)
            if shutil.which(checker) is None:
                out.append("(not installed)\n")
                continue
            try:
                diagnostics = _RUNNERS[checker](snippet_path)
            except BaseException as e:  # pytest.skip outside a test raises
                out.append(f"(unavailable: {e})\n")
                continue
            for lineno in sorted(diagnostics):
                out.append(f"line {lineno}: {lines[lineno - 1].strip()}")
                out.extend(f"    {message.splitlines()[0]}" for message in diagnostics[lineno])
            out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    print(_format_diagnostics())  # noqa: T201
