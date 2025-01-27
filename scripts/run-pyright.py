#!/usr/bin/env python
# ruff: noqa: T201

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import reduce
from itertools import groupby
from typing import Final, Optional, cast

import tomli
from typing_extensions import Literal, NotRequired, TypedDict

parser = argparse.ArgumentParser(
    prog="run-pyright",
    description=(
        "Run pyright for every specified pyright environment and print the merged results.\n\nBy"
        " default, the venv for each pyright environment is built using `requirements-pinned.txt`."
        " This speeds up venv construction on a development machine and in CI. Occasionally, these"
        " pinned requirements will need to be updated. To do this, pass `--update-pins`. This will"
        " cause the venv to be rebuilt with the looser requirements specified in"
        " `requirements.txt`, and `requirements-pinned.txt` updated with the resulting dependency"
        " list."
    ),
)

parser.add_argument(
    "--all",
    action="store_true",
    default=False,
    help=(
        "Run pyright for all environments. Environments are discovered by looking for directories"
        " at `pyright/envs/*`."
    ),
)


parser.add_argument(
    "--diff",
    action="store_true",
    default=False,
    help="Run pyright on the diff between the working tree and master.",
)

parser.add_argument(
    "--env",
    "-e",
    type=str,
    action="append",
    default=[],
    help=(
        "Names of pyright environment to run. Must be a directory in pyright/envs. Can be passed"
        " multiple times."
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
    help="If rebuilding pyright environments, do not use the uv cache. This is much slower but can be useful for debugging.",
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
        "Update `requirements-pinned.txt` for selected environments (implies `--rebuild`). The"
        " virtual env for the selected environment will be rebuilt using the abstract requirements"
        " specified in `requirements.txt`. After the environment is built, the full dependency list"
        " will be extracted with `uv pip freeze` and written to `requirements-pinned.txt` (this is"
        " what is used in CI and for building the default venv)."
    ),
)

parser.add_argument(
    "--skip-typecheck",
    action="store_true",
    default=False,
    help=(
        "Skip type checking, i.e. actually running pyright. This only makes sense when used together"
        " with `--rebuild` or `--update-pins` to build an environment."
    ),
)

parser.add_argument(
    "paths",
    type=str,
    nargs="*",
    help="Path to directories or python files to target with pyright.",
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
    character: int


class Range(TypedDict):
    start: Position
    end: Position


class Diagnostic(TypedDict):
    file: str
    message: str
    severity: str
    range: Range
    rule: NotRequired[str]


class Summary(TypedDict):
    filesAnalyzed: int
    errorCount: int
    warningCount: int
    informationCount: int
    timeInSec: float


class PyrightOutput(TypedDict):
    version: str
    time: str
    generalDiagnostics: Sequence[Diagnostic]
    summary: Summary


class RunResult(TypedDict):
    returncode: int
    output: PyrightOutput


class EnvPathSpec(TypedDict):
    env: str
    include: Sequence[str]
    exclude: Sequence[str]


# ########################
# ##### LOGIC
# ########################

PYRIGHT_ENV_ROOT: Final = "pyright"

DEFAULT_REQUIREMENTS_FILE: Final = "requirements.txt"


def get_env_path(env: str, rel_path: Optional[str] = None) -> str:
    env_root = os.path.join(PYRIGHT_ENV_ROOT, env)
    return os.path.abspath(os.path.join(env_root, rel_path) if rel_path else env_root)


def load_path_file(path: str) -> Sequence[str]:
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]


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
        targets = os.listdir(PYRIGHT_ENV_ROOT) if use_all else args.env or ["master"]
        for env in targets:
            if not os.path.exists(get_env_path(env)):
                raise Exception(f"Environment {env} not found in {PYRIGHT_ENV_ROOT}.")
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


def match_path(path: str, path_spec: EnvPathSpec) -> bool:
    for include in path_spec["include"]:
        if path.startswith(include):
            if not any(path.startswith(exclude) for exclude in path_spec["exclude"]):
                return True
    return False


def map_paths_to_envs(paths: Sequence[str]) -> Mapping[str, Sequence[str]]:
    env_path_specs: list[EnvPathSpec] = []
    for env in os.listdir(PYRIGHT_ENV_ROOT):
        include_path = get_env_path(env, "include.txt")
        exclude_path = get_env_path(env, "exclude.txt")
        env_path_specs.append(
            EnvPathSpec(
                env=env,
                include=load_path_file(include_path),
                exclude=load_path_file(exclude_path) if os.path.exists(exclude_path) else [],
            )
        )
    env_path_map: dict[str, list[str]] = {}
    for path in paths:
        if os.path.isdir(path) or os.path.splitext(path)[1] in [".py", ".pyi"]:
            env = next(
                (
                    env_path_spec["env"]
                    for env_path_spec in env_path_specs
                    if match_path(path, env_path_spec)
                ),
                None,
            )
            if env:
                env_path_map.setdefault(env, []).append(path)
    return env_path_map


def normalize_env(
    env: str, rebuild: bool, update_pins: bool, venv_python: str, no_cache: bool
) -> None:
    venv_path = os.path.join(get_env_path(env), ".venv")
    python_path = f"{venv_path}/bin/python"
    if (rebuild or update_pins) and os.path.exists(venv_path):
        print(f"Removing existing virtualenv for pyright environment {env}...")
        subprocess.run(f"rm -rf {venv_path}", shell=True, check=True)
    if not os.path.exists(venv_path):
        print(f"Creating virtualenv for pyright environment {env}...")
        if update_pins:
            src_requirements_path = get_env_path(env, "requirements.txt")
            extra_pip_install_args = []
        else:
            src_requirements_path = get_env_path(env, "requirements-pinned.txt")
            extra_pip_install_args = ["--no-deps"]
        dest_requirements_path = f"requirements-{env}.txt"

        # This is a hack to get around a bug in uv wherein "--editable-mode=compat" is not respected
        # if the package is in uv's global cache. This forces uv to reinstall the package and
        # thereby respect --editable-mode=compat, which is necessary to guarantee that pyright can
        # read the pth file for the editable install. Tracking uv issue here:
        #  https://github.com/astral-sh/uv/issues/7028
        reinstall_package_args = [
            f"--reinstall-package {pkg}" for pkg in get_all_editable_packages(env)
        ]

        build_venv_cmd = " && ".join(
            [
                f"uv venv --python={venv_python} --seed {venv_path}",
                f"uv pip install --python {python_path} -U pip setuptools wheel",
                " ".join(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        python_path,
                        # editable-mode=compat ensures dagster-internal editable installs are done
                        # in a way that is legible to pyright (i.e. not using import hooks). See:
                        #  https://github.com/microsoft/pyright/blob/main/docs/import-resolution.md#editable-installs
                        "--config-settings",
                        "editable-mode=compat",
                        "-r",
                        dest_requirements_path,
                        "--no-cache" if no_cache else "",
                        *extra_pip_install_args,
                        *reinstall_package_args,
                    ]
                ),
            ]
        )
        try:
            print(f"Copying {src_requirements_path} to {dest_requirements_path}....")
            shutil.copyfile(src_requirements_path, dest_requirements_path)
            subprocess.run(build_venv_cmd, shell=True, check=True)
            validate_editable_installs(env)
        except subprocess.CalledProcessError as e:
            subprocess.run(f"rm -rf {venv_path}", shell=True, check=True)
            print(f"Partially built virtualenv for pyright environment {env} deleted.")
            raise e
        finally:
            os.remove(dest_requirements_path)

        if update_pins:
            update_pinned_requirements(env)

    return None


def extract_package_name_from_editable_requirement(line: str) -> str:
    trailing_component = line.strip("/").rsplit("/", 1)[1]  # last component of requirement
    pkg = trailing_component.split("[")[0]  # remove extras if present
    return pkg.replace("-", "_")


def get_all_editable_packages(env: str) -> Sequence[str]:
    requirements = get_env_path(env, "requirements.txt")
    with open(requirements) as f:
        lines = [line.strip() for line in f.readlines()]
    return [
        extract_package_name_from_editable_requirement(line)
        for line in lines
        if line.startswith("-e")
    ]


# This ensures that all of our editable installs are "legacy" style, which is required to work with
# pyright.
def validate_editable_installs(env: str) -> None:
    venv_path = os.path.join(get_env_path(env), ".venv")
    for pth_file in glob.glob(f"{venv_path}/lib/python*/site-packages/__editable__*.pth"):
        with open(pth_file) as f:
            first_line = f.readlines()[0]
        # Not a legacy pth-- all legacy pth files contain an absolute path on the first line
        if first_line[0] != "/":
            raise Exception(f"Found unexpected modern-style pth file in env: {pth_file}.")


def update_pinned_requirements(env: str) -> None:
    print(f"Updating pinned requirements for pyright environment {env}...")
    venv_path = os.path.join(get_env_path(env), ".venv")
    python_path = f"{venv_path}/bin/python"
    raw_dep_list = subprocess.run(
        f"uv pip freeze --python={python_path}",
        capture_output=True,
        shell=True,
        text=True,
        check=True,
    ).stdout

    if os.path.exists("python_modules/dagster"):  # in oss
        resolved_oss_root = os.getcwd()
        dep_list = re.sub(f"-e file://{resolved_oss_root}/(.+)", "-e \\1", raw_dep_list)
    else:  # in internal
        resolved_oss_root = os.environ["DAGSTER_GIT_REPO_DIR"].rstrip("/")
        resolved_internal_root = os.getcwd()
        dep_list = re.sub(
            f"-e file://{resolved_oss_root}/(.+)", "-e ${DAGSTER_GIT_REPO_DIR}/\\1", raw_dep_list
        )
        dep_list = re.sub(f"-e file://{resolved_internal_root}/(.+)", "-e \\1", dep_list)

    with open(get_env_path(env, "requirements-pinned.txt"), "w") as f:
        f.write(dep_list)


def run_pyright(
    env: str,
    paths: Optional[Sequence[str]],
    rebuild: bool,
    pinned_deps: bool,
    venv_python: str,
) -> RunResult:
    with temp_pyright_config_file(env) as config_path:
        base_pyright_cmd = " ".join(
            [
                "pyright",
                f"--project={config_path}",
                "--outputjson",
                "--level=warning",
                "--warnings",  # Error on warnings
            ]
        )
        shell_cmd = " \\\n".join([base_pyright_cmd, *[f"    {p}" for p in paths or []]])
        print(f"Running pyright for environment `{env}`...")
        print(f"  {shell_cmd}")
        result = subprocess.run(shell_cmd, capture_output=True, shell=True, text=True, check=False)
        try:
            json_result = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = (result.stdout == "" and result.stderr) or result.stdout
            raise Exception(f"Pyright output was not valid JSON. Output was:\n\n{output}")
    return {
        "returncode": result.returncode,
        "output": cast(PyrightOutput, json_result),
    }


@contextmanager
def temp_pyright_config_file(env: str) -> Iterator[str]:
    with open("pyproject.toml", encoding="utf-8") as f:
        toml = tomli.loads(f.read())
    config = toml["tool"]["pyright"]
    config["venvPath"] = f"{PYRIGHT_ENV_ROOT}/{env}"
    include_path = get_env_path(env, "include.txt")
    exclude_path = get_env_path(env, "exclude.txt")
    config["include"] = load_path_file(include_path)
    if os.path.exists(exclude_path):
        config["exclude"] += load_path_file(exclude_path)
    temp_config_path = f"pyrightconfig-{env}.json"
    print("Creating temporary pyright config file at", temp_config_path)
    try:
        with open(temp_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)
        yield temp_config_path
    finally:
        os.remove(temp_config_path)


def merge_pyright_results(result_1: RunResult, result_2: RunResult) -> RunResult:
    returncode = 1 if 1 in (result_1["returncode"], result_2["returncode"]) else 0
    output_1, output_2 = (result["output"] for result in (result_1, result_2))
    summary = {}
    for key in output_1["summary"].keys():
        summary[key] = output_1["summary"][key] + output_2["summary"][key]
    diagnostics = [*output_1["generalDiagnostics"], *output_2["generalDiagnostics"]]
    return {
        "returncode": returncode,
        "output": {
            "time": output_1["time"],
            "version": output_1["version"],
            "summary": cast(Summary, summary),
            "generalDiagnostics": diagnostics,
        },
    }


def print_output(result: RunResult, output_json: bool) -> None:
    if output_json:
        print(json.dumps(result["output"], indent=2))
    else:
        print_report(result)


def get_dagster_pyright_version() -> str:
    dagster_setup = os.path.abspath(os.path.join(__file__, "../../python_modules/dagster/setup.py"))
    with open(dagster_setup, encoding="utf-8") as f:
        content = f.read()
    m = re.search('"pyright==([^"]+)"', content)
    assert m is not None, "Could not find pyright version in python_modules/dagster/setup.py"
    return m.group(1)


def get_hints(output: PyrightOutput) -> Sequence[str]:
    hints: list[str] = []

    if any(
        "rule" in diag and diag["rule"] == "reportMissingImports"
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
                        " `make rebuild_pyright_pins` to rebuild and update the"
                        " dependencies of the pyright venv."
                    ),
                    (
                        "If you have added an entirely new package, add it to"
                        " pyright/master/requirements.txt and then run `make rebuild_pyright_pins`."
                    ),
                ]
            )
        )

    dagster_pyright_version = get_dagster_pyright_version()
    if dagster_pyright_version != output["version"]:
        hints.append(
            f'Your local version of pyright is {output["version"]}, which does not match Dagster\'s'
            f" pinned version of {dagster_pyright_version}. Please run `make install_pyright` to"
            " install the correct version."
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
    print(f"pyright {output['version']}")
    print(f"Finished in {summary['timeInSec']} seconds")
    print(f"Analyzed {summary['filesAnalyzed']} files")
    print(f"Found {summary['errorCount']} errors")
    print(f"Found {summary['warningCount']} warnings")

    for hint in get_hints(output):
        print("\n" + hint)


if __name__ == "__main__":
    assert sys.version_info < (3, 12), (
        "This script is not currently compatible with Python 3.12+ "
        "because of `dagster-airflow[test_airflow_2]`.",
    )
    assert os.path.exists(".git"), "Must be run from the root of the repository"
    args = parser.parse_args()
    params = get_params(args)
    if params["mode"] == "path":
        env_path_map = map_paths_to_envs(params["targets"])
    else:
        env_path_map = {env: None for env in params["targets"]}

    for env in env_path_map:
        normalize_env(
            env, params["rebuild"], params["update_pins"], params["venv_python"], params["no_cache"]
        )
    if params["skip_typecheck"]:
        print("Successfully built environments. Skipping typecheck.")
    elif len(env_path_map) == 0:
        print("No paths to analyze. Skipping typecheck.")
    elif not params["skip_typecheck"]:
        run_results = [
            run_pyright(
                env,
                paths=env_path_map[env],
                rebuild=params["rebuild"],
                pinned_deps=params["update_pins"],
                venv_python=params["venv_python"],
            )
            for env in env_path_map
        ]
        merged_result = reduce(merge_pyright_results, run_results)
        print_output(merged_result, params["json"])
        sys.exit(merged_result["returncode"])
