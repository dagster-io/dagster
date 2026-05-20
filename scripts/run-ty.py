#!/usr/bin/env python

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import cache, reduce
from itertools import groupby
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast

import tomllib

parser = argparse.ArgumentParser(
    prog="run-ty",
    description=(
        "Run ty for every specified ty environment and print the merged results.\n\nEach"
        " environment is a directory containing `pyproject.toml` (with `[tool.ty.*]`"
        " config and the source-of-truth dep list) and `uv.lock` (pinned resolved tree)."
        " Declare envs with one or more `--env-dir <dir>` flags; when none are passed,"
        " the script falls back to scanning `<cwd>/ty/<env>/`. The venv is built by"
        " `uv sync` against the lockfile. Pass `--update-pins` to refresh `uv.lock` to"
        " the newest versions matching the pyproject constraints."
    ),
)

parser.add_argument(
    "--all",
    action="store_true",
    default=False,
    help="Run ty for every declared environment (default when no targeting flag is passed).",
)


parser.add_argument(
    "--diff",
    action="store_true",
    default=False,
    help="Run ty on the diff between the working tree and master.",
)

parser.add_argument(
    "--env-dir",
    type=str,
    action="append",
    default=[],
    dest="env_dirs",
    help=(
        "Declare a ty environment by its directory (relative to cwd or absolute)."
        " The directory must contain `pyproject.toml` (with `[tool.ty.*]` config) and"
        " `uv.lock`. Kind is auto-detected: `[tool.uv.workspace]` present → workspace"
        " (ty installed via the workspace's `ty` extra), absent → project (ty pulled"
        " via `uv tool run --from ty==<pin>`). Repeatable. If omitted, falls back to"
        " scanning `<cwd>/ty/<env>/`."
    ),
)

parser.add_argument(
    "--env",
    "-e",
    type=str,
    action="append",
    default=[],
    help=(
        "Names of ty environment to run. Must match an env declared via `--env-dir`"
        " (or discovered by the fallback scan). Can be passed multiple times."
    ),
)

parser.add_argument(
    "--json",
    action="store_true",
    default=False,
    help="Output results in JSON format.",
)

parser.add_argument(
    "--no-cache",
    action="store_true",
    default=False,
    help="If rebuilding ty environments, do not use the uv cache. This is much slower but can be useful for debugging.",
)

parser.add_argument(
    "--rebuild",
    "-r",
    action="store_true",
    default=False,
    help="Force rebuild of virtual environment.",
)

parser.add_argument(
    "--update-pins",
    action="store_true",
    default=False,
    help=(
        "Refresh `uv.lock` for selected environments to the newest versions matching the"
        " `pyproject.toml` constraints, then sync the venv to match. Equivalent to"
        " `uv lock --upgrade` followed by `uv sync --frozen`."
    ),
)

parser.add_argument(
    "--skip-typecheck",
    action="store_true",
    default=False,
    help=(
        "Skip type checking, i.e. actually running ty. This only makes sense when used together"
        " with `--rebuild` or `--update-pins` to build an environment."
    ),
)

parser.add_argument(
    "paths",
    type=str,
    nargs="*",
    help="Path to directories or python files to target with ty.",
)

# ########################
# ##### TYPES
# ########################


class Params(TypedDict):
    mode: Literal["env", "path"]
    targets: Sequence[str]
    json: bool
    no_cache: bool
    rebuild: bool
    update_pins: bool
    venv_python: str
    skip_typecheck: bool


class Position(TypedDict):
    line: int
    column: int


class Positions(TypedDict):
    begin: Position
    end: Position


class Location(TypedDict):
    path: str
    positions: Positions


class TyDiagnostic(TypedDict):
    check_name: str
    description: str
    severity: str
    fingerprint: str
    location: Location


class Diagnostic(TypedDict):
    file: str
    message: str
    severity: str
    range: dict
    rule: NotRequired[str]


class Summary(TypedDict):
    filesAnalyzed: int
    errorCount: int
    warningCount: int
    informationCount: int
    timeInSec: float


class TyOutput(TypedDict):
    version: str
    time: str
    generalDiagnostics: Sequence[Diagnostic]
    summary: Summary


class RunResult(TypedDict):
    returncode: int
    output: TyOutput


class EnvSpec(TypedDict):
    name: str
    kind: Literal["project", "workspace"]
    path: Path  # absolute — directory with pyproject.toml + uv.lock + .venv
    project_root: Path  # absolute — dir ty treats as project root when checking this env


# ########################
# ##### LOGIC
# ########################

# Fallback dir name scanned when no `--env-dir` args are passed.
_TY_ENV_ROOT_DIR = "ty"

# Populated once by `initialize_envs` from argparse. Read-only after that.
_ENVS: dict[str, EnvSpec] = {}


def _project_root_for_env(env_path: Path, workspace_root: Path) -> Path:
    """Convention: ty's project root for an env is `workspace_root/dagster-oss` if
    the env dir is anywhere under `dagster-oss/`, otherwise `workspace_root`.

    The env's `[tool.ty.src].include` paths are evaluated relative to this
    directory. ty anchors include paths to the project root (= directory
    of the discovered config file or cwd when `--config-file` is used)
    and rejects `..` in include globs, so the project root has to be at
    or above the code being checked. Splitting by dagster-oss/ vs. not
    keeps the OSS-only envs anchored at `dagster-oss/` while internal
    envs anchor at the worktree root.
    """
    dagster_oss = workspace_root / "dagster-oss"
    try:
        env_path.relative_to(dagster_oss)
        return dagster_oss
    except ValueError:
        return workspace_root


def _build_env_spec(env_dir: str | Path) -> EnvSpec:
    """Build an EnvSpec from a directory containing `pyproject.toml` + `uv.lock`.

    Kind is auto-detected: presence of `[tool.uv.workspace]` ⟹ workspace,
    absence ⟹ project. Project root (where ty considers paths anchored)
    comes from `_project_root_for_env`. Name = resolved dir's basename,
    with the special case `cwd / "."` ⟹ "internal" so the typical
    repo-root workspace env keeps a stable label even though its dir's
    basename is whatever the worktree happens to be called.
    """
    cwd = Path(os.getcwd()).resolve()
    raw = Path(env_dir)
    abs_path = (cwd / raw).resolve() if not raw.is_absolute() else raw.resolve()
    pyproject = abs_path / "pyproject.toml"
    if not pyproject.exists():
        raise Exception(f"`--env-dir {env_dir}`: no pyproject.toml at {pyproject}")
    if not (abs_path / "uv.lock").exists():
        raise Exception(f"`--env-dir {env_dir}`: no uv.lock at {abs_path / 'uv.lock'}")
    with open(pyproject, "rb") as f:
        toml_data = tomllib.load(f)
    if "ty" not in toml_data.get("tool", {}):
        raise Exception(
            f"`--env-dir {env_dir}`: pyproject.toml at {pyproject} has no `[tool.ty]`"
            f" section. The env's ty config must live in its own pyproject.toml."
        )
    is_workspace = "workspace" in toml_data.get("tool", {}).get("uv", {})
    kind: Literal["project", "workspace"] = "workspace" if is_workspace else "project"
    name = "internal" if is_workspace and abs_path == cwd else abs_path.name
    project_root = _project_root_for_env(abs_path, cwd)
    return EnvSpec(name=name, kind=kind, path=abs_path, project_root=project_root)


def initialize_envs(env_dirs: Sequence[str]) -> None:
    """Populate the env registry.

    If `env_dirs` is provided, each entry must be a directory containing
    `pyproject.toml` + `uv.lock`. Otherwise we fall back to scanning
    `<cwd>/ty/<name>/` and treating each matching dir as a project-kind
    env. The fallback exists so the script also works post-OSS-sync,
    where `just ty` (and its `--env-dir` args) doesn't exist.
    """
    _ENVS.clear()
    if env_dirs:
        for d in env_dirs:
            spec = _build_env_spec(d)
            _ENVS[spec["name"]] = spec
        return
    cwd = Path(os.getcwd()).resolve()
    ty_root = cwd / _TY_ENV_ROOT_DIR
    if ty_root.exists():
        for d in sorted(ty_root.iterdir()):
            if d.is_dir() and (d / "pyproject.toml").exists() and (d / "uv.lock").exists():
                spec = _build_env_spec(d)
                _ENVS[spec["name"]] = spec


def _populate_envs() -> Mapping[str, EnvSpec]:
    return _ENVS


def _discover_envs() -> Sequence[str]:
    """Return sorted env names from the populated registry."""
    return sorted(_populate_envs().keys())


def get_env(name: str) -> EnvSpec:
    envs = _populate_envs()
    if name not in envs:
        raise Exception(f"Environment {name} not found.")
    return envs[name]


def get_env_path(name: str) -> Path:
    return get_env(name)["path"]


@cache
def get_dagster_ty_version() -> str:
    """Read the pinned ty version from `python_modules/dagster/pyproject.toml`.

    The version lives in dagster's `[project.optional-dependencies].ty` so it
    sits alongside the stub packages and is bumped via the same lockfile workflow.
    """
    dagster_pyproject = os.path.abspath(
        os.path.join(__file__, "../../python_modules/dagster/pyproject.toml")
    )
    with open(dagster_pyproject, "rb") as f:
        pyproject = tomllib.load(f)
    ty_deps = pyproject.get("project", {}).get("optional-dependencies", {}).get("ty", [])
    for dep in ty_deps:
        if dep.startswith("ty=="):
            return dep.split("==")[1]
    raise RuntimeError(
        "Could not find a `ty==` entry in"
        " python_modules/dagster/pyproject.toml's [project.optional-dependencies].ty"
    )


def load_env_ty_config(env: str) -> Mapping[str, Any]:
    """Read the env's `[tool.ty.*]` table from its own pyproject.toml."""
    spec = get_env(env)
    with open(spec["path"] / "pyproject.toml", "rb") as f:
        toml_data = tomllib.load(f)
    return toml_data.get("tool", {}).get("ty", {})


def load_env_include_paths(env: str) -> Sequence[Path]:
    """Resolve `[tool.ty.src].include` from the env's pyproject.toml to absolute paths.

    Includes are anchored to the env's project root (per
    `_project_root_for_env` — `dagster-oss/` for OSS envs, workspace
    root otherwise). Used for `--diff` path-routing.
    """
    spec = get_env(env)
    include = load_env_ty_config(env).get("src", {}).get("include", [])
    return [(spec["project_root"] / p).resolve() for p in include]


def get_params(args: argparse.Namespace) -> Params:
    if args.all and (args.diff or args.env or args.paths):
        raise Exception(
            "Cannot target specific environments, paths, or diff simultaneously with --all."
        )
    elif args.diff and (args.env or args.paths):
        raise Exception("Cannot target specific environments or paths, simultaneously with --diff.")
    elif len(args.paths) >= 1 and len(args.env) >= 1:
        raise Exception("Cannot pass both paths and environments.")
    use_all = args.all or not (args.diff or args.env or args.paths)
    mode: Literal["env", "path"]
    if args.env or use_all:
        mode = "env"
        targets = _discover_envs() if use_all else args.env or ["master"]
        for env in targets:
            # raises if missing
            get_env(env)
    elif args.diff:
        mode = "path"
        targets = (
            subprocess.check_output(
                ["git", "diff", "--name-only", "origin/master", "--diff-filter=d"]
            )
            .decode("utf-8")
            .splitlines()
        )
        if not targets:
            print("No paths changed in diff.")
            sys.exit(0)
    else:
        mode = "path"
        targets = args.paths

    venv_python = (
        subprocess.run(["which", "python"], check=True, capture_output=True).stdout.decode().strip()
    )
    return Params(
        mode=mode,
        targets=targets,
        update_pins=args.update_pins,
        json=args.json,
        rebuild=args.rebuild,
        no_cache=args.no_cache,
        venv_python=venv_python,
        skip_typecheck=args.skip_typecheck,
    )


def _path_under(child: Path, parent: Path) -> bool:
    """True if `child` is `parent` or a descendant of `parent`."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def map_paths_to_envs(paths: Sequence[str]) -> Mapping[str, Sequence[str]]:
    """Route a list of repo-relative paths to the env that owns each one.

    Each env's include paths are resolved to absolute paths (anchored at
    its pyproject.toml's directory). Input paths are resolved against cwd
    (the internal repo root) and prefix-matched. First env wins.
    """
    cwd = Path(os.getcwd()).resolve()
    env_includes = {env: load_env_include_paths(env) for env in _discover_envs()}
    env_path_map: dict[str, list[str]] = {}
    for path in paths:
        path_obj = Path(path)
        if not (path_obj.is_dir() or path_obj.suffix in [".py", ".pyi"]):
            continue
        path_abs = (cwd / path).resolve()
        for env, includes in env_includes.items():
            if any(_path_under(path_abs, inc) for inc in includes):
                env_path_map.setdefault(env, []).append(path)
                break
    return env_path_map


def normalize_env(
    env: str,
    *,
    rebuild: bool,
    update_pins: bool,
    venv_python: str,
    no_cache: bool,
) -> None:
    """Ensure the env's venv matches its lockfile.

    For `project`-kind envs:
    - `--update-pins`: refresh `uv.lock` to newest matching versions, then sync.
    - `--rebuild`: blow away the venv and re-create from `uv.lock`.
    - default: `uv sync --frozen` (no resolution, just install the locked set).

    `editable-mode=compat` is set via `--config-setting` so editable in-repo
    installs land as legacy `.pth` files that ty can read. Tracking uv bug:
        https://github.com/astral-sh/uv/issues/7028

    For `workspace`-kind envs:
    The venv is user-managed (`just sync` from the workspace root), so this
    is a near-no-op — we just warn that `--rebuild` and `--update-pins` don't
    apply.
    """
    spec = get_env(env)

    if spec["kind"] == "workspace":
        if rebuild or update_pins:
            print(
                f"Warning: --rebuild / --update-pins do not apply to workspace env `{env}`; skipping."
            )
        return

    env_root = spec["path"]
    venv_path = env_root / ".venv"

    if rebuild and venv_path.exists():
        print(f"Removing existing virtualenv for ty environment {env}...")
        shutil.rmtree(venv_path)

    if update_pins:
        print(f"Refreshing uv.lock for ty environment {env}...")
        subprocess.run(
            ["uv", "lock", "--upgrade", "--no-cache"] if no_cache else ["uv", "lock", "--upgrade"],
            cwd=env_root,
            check=True,
        )

    if not venv_path.exists():
        print(f"Creating virtualenv for ty environment {env}...")
    cmd = [
        "uv",
        "sync",
        "--frozen",
        "--python",
        venv_python,
        "--config-setting",
        "editable-mode=compat",
    ]
    if no_cache:
        cmd.append("--no-cache")
    try:
        subprocess.run(cmd, cwd=env_root, check=True)
        validate_editable_installs(env)
    except subprocess.CalledProcessError:
        if venv_path.exists():
            shutil.rmtree(venv_path)
            print(f"Partially built virtualenv for ty environment {env} deleted.")
        raise


# Ensures all editable installs are "legacy" style (`__editable__*.pth` with an
# absolute path on the first line). Modern-style uv editables use a custom
# `MetaPathFinder` that ty cannot follow.
#
# Skipped for `workspace`-kind envs whose venv is owned by the user's normal
# `just sync` workflow and may legitimately contain modern-style entries.
def validate_editable_installs(env: str) -> None:
    spec = get_env(env)
    if spec["kind"] == "workspace":
        return
    venv_path = spec["path"] / ".venv"
    for pth_file in glob.glob(f"{venv_path}/lib/python*/site-packages/__editable__*.pth"):
        with open(pth_file, encoding="utf-8") as f:
            first_line = f.readlines()[0]
        # Not a legacy pth-- all legacy pth files contain an absolute path on the first line
        if first_line[0] != "/":
            raise Exception(f"Found unexpected modern-style pth file in env: {pth_file}.")


def _serialize_ty_config(config: Mapping[str, Any]) -> str:
    """Translate an env pyproject's `[tool.ty.*]` dict into ty.toml format.

    ty's `--config-file` accepts only top-level ty.toml — `environment`,
    `src`, `rules`, `overrides`, etc. — not the `[tool.ty.*]` namespace
    that lives in pyproject. So we strip the prefix and emit a flat
    table-per-section file. Handles three table shapes that appear in
    `[tool.ty.*]`:
    - dict[str, scalar | list]: emitted as a `[name]` table with key=value lines.
    - dict containing nested dicts: emits the parent's scalars first, then a
      `[name.child]` table for each nested dict (TOML ordering requirement).
    - list[dict]: emitted as repeated `[[name]]` array-of-tables blocks (e.g.
      `overrides`).
    """
    sections: list[str] = []
    for section_name, section_body in config.items():
        if isinstance(section_body, list):
            for item in section_body:
                sections.append(_serialize_section(section_name, item, array_of_tables=True))
        else:
            sections.append(_serialize_section(section_name, section_body, array_of_tables=False))
    return "\n\n".join(sections) + "\n"


def _serialize_section(name: str, body: Mapping[str, Any], *, array_of_tables: bool) -> str:
    header = f"[[{name}]]" if array_of_tables else f"[{name}]"
    lines = [header]
    scalars = {k: v for k, v in body.items() if not isinstance(v, Mapping)}
    nested = {k: v for k, v in body.items() if isinstance(v, Mapping)}
    for k, v in scalars.items():
        lines.append(f"{k} = {_toml_value(v)}")
    for k, v in nested.items():
        lines.append("")
        # Nested tables under an array-of-tables item use the same dotted-key
        # syntax (`[name.child]`) — TOML scopes them to the most recent
        # `[[name]]` block.
        lines.append(_serialize_section(f"{name}.{k}", v, array_of_tables=False))
    return "\n".join(lines)


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    if isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"Unsupported TOML value type: {type(value).__name__}")


@contextmanager
def _temp_ty_config(env: str) -> Iterator[Path]:
    """Write the env's `[tool.ty.*]` as a top-level ty.toml at its project root.

    ty needs to read the env's config but treat the env's *project root*
    (not the env dir, not the env pyproject's dir) as the include-path
    anchor. We achieve that by translating the env pyproject's
    `[tool.ty]` into top-level ty.toml format and dropping it at
    `<project_root>/.ty-<env>.toml` for the duration of the run, then
    invoking ty with `cwd=<project_root>` and
    `--config-file=<temp>`. The file is gitignored (`/.ty-*.toml` and
    `/dagster-oss/.ty-*.toml` patterns) and deleted on context exit.
    """
    spec = get_env(env)
    config = load_env_ty_config(env)
    if not config:
        raise Exception(f"env `{env}` has no [tool.ty] in pyproject.toml")
    temp_path = spec["project_root"] / f".ty-{env}.toml"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(_serialize_ty_config(config))
    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)


def convert_ty_diagnostic_to_pyright_format(ty_diag: TyDiagnostic) -> Diagnostic:
    """Convert ty's gitlab format diagnostic to pyright-compatible format."""
    return Diagnostic(
        file=ty_diag["location"]["path"],
        message=ty_diag["description"],
        severity="error" if ty_diag["severity"] == "major" else "warning",
        range={
            "start": {
                "line": ty_diag["location"]["positions"]["begin"]["line"] - 1,  # 0-indexed
                "character": ty_diag["location"]["positions"]["begin"]["column"] - 1,
            },
            "end": {
                "line": ty_diag["location"]["positions"]["end"]["line"] - 1,
                "character": ty_diag["location"]["positions"]["end"]["column"] - 1,
            },
        },
        rule=ty_diag["check_name"],
    )


def _run_ty_workspace(env: str, paths: Sequence[str] | None) -> RunResult:
    """Run ty against a workspace-kind env via `uv run --extra ty`.

    The env's `[tool.ty.*]` (in its own pyproject.toml) is translated to
    a temp ty.toml at the project root and passed via `--config-file`;
    cwd is set to the project root so include paths anchor there. The
    workspace's own pinned `ty` from the `ty` extra is used, so no
    `--from ty==...`.
    """
    start_time = time.time()

    spec = get_env(env)
    env_root = spec["path"]
    project_root = spec["project_root"]
    invoking_cwd = Path(os.getcwd()).resolve()

    with _temp_ty_config(env) as config_path:
        base_ty_cmd_parts = [
            "uv",
            "run",
            "--frozen",
            "--isolated",
            "--extra",
            "ty",
            "ty",
            "check",
            f"--config-file={config_path}",
            "--error-on-warning",
            "-v",
            "--output-format=gitlab",
        ]
        check_paths = [str((invoking_cwd / p).resolve()) for p in (paths or [])]
        shell_cmd = " \\\n".join([" ".join(base_ty_cmd_parts), *[f"    {p}" for p in check_paths]])
        print(f"Running ty for environment `{env}`...")
        print(f"  {shell_cmd}")
        result = subprocess.run(
            shell_cmd,
            capture_output=True,
            shell=True,
            text=True,
            check=False,
            cwd=project_root,
        )

    elapsed_time = time.time() - start_time

    return _build_run_result(
        env=env,
        result=result,
        elapsed_time=elapsed_time,
        check_paths=check_paths,
        version_cmd=[
            "uv",
            "run",
            "--frozen",
            "--isolated",
            "--extra",
            "ty",
            "ty",
            "version",
        ],
        version_cwd=env_root,
    )


def _run_ty_project(env: str, paths: Sequence[str] | None) -> RunResult:
    """Run ty against a project-kind env via `uv tool run --from ty==<version>`.

    The env's `[tool.ty.*]` (in its own pyproject.toml) is translated to
    a temp ty.toml at the project root and passed via `--config-file`;
    cwd is set to the project root so include paths anchor there. The
    env's `.venv` is supplied via `--python`. Diff-routed paths arrive
    repo-relative; they're resolved against the invoking cwd and passed
    to ty as absolute paths.
    """
    start_time = time.time()

    spec = get_env(env)
    env_root = spec["path"]
    project_root = spec["project_root"]
    venv_path = env_root / ".venv"
    python_path = f"{venv_path}/bin/python"
    invoking_cwd = Path(os.getcwd()).resolve()

    with _temp_ty_config(env) as config_path:
        base_ty_cmd_parts = [
            "uv",
            "tool",
            "run",
            "--from",
            f"ty=={get_dagster_ty_version()}",
            "ty",
            "check",
            f"--config-file={config_path}",
            f"--python={python_path}",
            "--output-format=gitlab",
            "--error-on-warning",
            # `-v` makes ty emit "INFO Indexed N file(s) in ...s" to stderr,
            # which we parse below to populate filesAnalyzed accurately.
            # Without this we have no way to know how many files ty visited.
            "-v",
        ]

        # Diff-routed paths arrive repo-relative; resolve to absolute so
        # cwd=project_root doesn't break interpretation. Empty list means
        # ty uses the include paths from the temp config.
        check_paths = [str((invoking_cwd / p).resolve()) for p in (paths or [])]

        shell_cmd = " \\\n".join([" ".join(base_ty_cmd_parts), *[f"    {p}" for p in check_paths]])
        print(f"Running ty for environment `{env}`...")
        print(f"  {shell_cmd}")
        result = subprocess.run(
            shell_cmd,
            capture_output=True,
            shell=True,
            text=True,
            check=False,
            cwd=project_root,
        )

    elapsed_time = time.time() - start_time

    return _build_run_result(
        env=env,
        result=result,
        elapsed_time=elapsed_time,
        check_paths=check_paths,
        version_cmd=[
            "uv",
            "tool",
            "run",
            "--from",
            f"ty=={get_dagster_ty_version()}",
            "ty",
            "version",
        ],
        version_cwd=None,
    )


def _build_run_result(
    *,
    env: str,
    result: subprocess.CompletedProcess[str],
    elapsed_time: float,
    check_paths: Sequence[str],
    version_cmd: Sequence[str],
    version_cwd: Path | None,
) -> RunResult:
    # ty exits 0 = success, 1 = diagnostics emitted (JSON on stdout),
    # 2 = ty itself errored before producing JSON (config error, panic, etc.)
    # with the failure message on stderr. Surface case 2 so it doesn't
    # silently masquerade as a clean run with zero diagnostics.
    if result.returncode != 0 and not result.stdout.strip():
        raise RuntimeError(
            f"ty exited {result.returncode} for env `{env}` with no JSON output."
            f" stderr:\n\n{result.stderr}"
        )
    try:
        ty_diagnostics: list[TyDiagnostic] = (
            json.loads(result.stdout) if result.stdout.strip() else []
        )
    except json.JSONDecodeError:
        output = (result.stdout == "" and result.stderr) or result.stdout
        raise RuntimeError(f"ty output for env `{env}` was not valid JSON. Output was:\n\n{output}")

    diagnostics = [convert_ty_diagnostic_to_pyright_format(d) for d in ty_diagnostics]

    error_count = sum(1 for d in ty_diagnostics if d["severity"] == "major")
    warning_count = sum(1 for d in ty_diagnostics if d["severity"] != "major")

    version_result = subprocess.run(
        list(version_cmd),
        capture_output=True,
        text=True,
        check=False,
        cwd=version_cwd,
    )
    ty_version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"

    # Parse the file count from ty's verbose stderr output ("INFO Indexed N file(s)").
    # If ty re-indexes mid-run, multiple lines may appear — sum them.
    indexed_matches = re.findall(r"^INFO Indexed (\d+) file\(s\)", result.stderr, re.MULTILINE)
    if indexed_matches:
        files_analyzed = sum(int(n) for n in indexed_matches)
    else:
        # Fall back to counting file-typed entries in check_paths. This undercounts
        # when entries are directories, but it's the best we can do without verbose output.
        files_analyzed = len([p for p in check_paths if Path(p).is_file()]) if check_paths else 0

    return {
        "returncode": result.returncode,
        "output": {
            "version": ty_version,
            "time": f"{elapsed_time:.2f}s",
            "generalDiagnostics": diagnostics,
            "summary": {
                "filesAnalyzed": files_analyzed,
                "errorCount": error_count,
                "warningCount": warning_count,
                "informationCount": 0,
                "timeInSec": elapsed_time,
            },
        },
    }


def run_ty(
    env: str,
    paths: Sequence[str] | None,
) -> RunResult:
    spec = get_env(env)
    if spec["kind"] == "workspace":
        return _run_ty_workspace(env, paths)
    return _run_ty_project(env, paths)


def merge_ty_results(result_1: RunResult, result_2: RunResult) -> RunResult:
    # ty exits 0 = success, 1 = diagnostics found, 2 = ty itself errored
    # (e.g. invalid config). Propagate any non-zero return code so that
    # ty failures surface instead of silently masquerading as 0-error runs.
    returncode = max(result_1["returncode"], result_2["returncode"])
    output_1, output_2 = (result["output"] for result in (result_1, result_2))
    summary_1 = cast("dict[str, Any]", output_1["summary"])
    summary_2 = cast("dict[str, Any]", output_2["summary"])
    summary = {key: summary_1[key] + summary_2[key] for key in summary_1}
    diagnostics = [*output_1["generalDiagnostics"], *output_2["generalDiagnostics"]]
    return {
        "returncode": returncode,
        "output": {
            "time": output_1["time"],
            "version": output_1["version"],
            "summary": cast("Summary", summary),
            "generalDiagnostics": diagnostics,
        },
    }


def print_output(result: RunResult, output_json: bool) -> None:
    if output_json:
        print(json.dumps(result["output"], indent=2))
    else:
        print_report(result)


def get_hints(output: TyOutput) -> Sequence[str]:
    hints: list[str] = []

    if any(
        "rule" in diag and diag["rule"] == "unresolved-import"
        for diag in output["generalDiagnostics"]
    ):
        hints.append(
            "\n".join(
                [
                    (
                        "At least one error was caused by a missing import. This is often caused by"
                        " changing package dependencies."
                    ),
                    (
                        "If you have added dependencies to an existing package, run"
                        " `just rebuild_ty_pins` to rebuild and update the"
                        " dependencies of the ty venv."
                    ),
                    (
                        "If you have added an entirely new package, add it to"
                        " ty/master/pyproject.toml and then run `just rebuild_ty_pins`."
                    ),
                ]
            )
        )

    return hints


def print_report(result: RunResult) -> None:
    output = result["output"]
    diags = sorted(output["generalDiagnostics"], key=lambda diag: diag["file"])

    print()  # blank line makes it more readable when run from `make`

    # diagnostics
    for file, file_diags in groupby(diags, key=lambda diag: diag["file"]):
        print(f"{file}:")
        for x in file_diags:
            range_str = f"{x['range']['start']['line'] + 1}:{x['range']['start']['character']}"
            head_str = f"  {range_str}: {x['message']}"
            rule_str = f"({x['rule']})" if "rule" in x else None
            full_str = " ".join(filter(None, (head_str, rule_str)))
            print(full_str + "\n")  # extra blank line for readability

    # summary
    summary = output["summary"]
    print(f"ty {output['version']}")
    print(f"Finished in {summary['timeInSec']:.2f} seconds")
    print(f"Analyzed {summary['filesAnalyzed']} files")
    print(f"Found {summary['errorCount']} errors")
    print(f"Found {summary['warningCount']} warnings")

    for hint in get_hints(output):
        print("\n" + hint)


if __name__ == "__main__":
    args = parser.parse_args()
    initialize_envs(args.env_dirs)
    params = get_params(args)
    if params["mode"] == "path":
        env_path_map = map_paths_to_envs(params["targets"])
    else:
        env_path_map = {env: None for env in params["targets"]}

    for env in env_path_map:
        normalize_env(
            env,
            rebuild=params["rebuild"],
            update_pins=params["update_pins"],
            venv_python=params["venv_python"],
            no_cache=params["no_cache"],
        )
    if params["skip_typecheck"]:
        print("Successfully built environments. Skipping typecheck.")
    elif len(env_path_map) == 0:
        print("No paths to analyze. Skipping typecheck.")
    elif not params["skip_typecheck"]:
        run_results = [run_ty(env, paths=env_path_map[env]) for env in env_path_map]
        merged_result = reduce(merge_ty_results, run_results)
        print_output(merged_result, params["json"])
        sys.exit(merged_result["returncode"])
