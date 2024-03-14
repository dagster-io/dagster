#!/usr/bin/env python
# ruff: noqa: T201

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from functools import reduce
from itertools import groupby
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, cast

import tomli
from typing_extensions import Final, Literal, NotRequired, TypedDict

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
    "--unannotated",
    action="store_true",
    default=False,
    help="Analyze unannotated functions. This is not currently used in CI.",
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
    unannotated: bool
    mode: Literal["env", "path"]
    targets: Sequence[str]
    json: bool
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
    with open(path, "r", encoding="utf-8") as f:
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
        targets = args.pathsBUILDKIT

    venv_python = (
        subprocess.run(["which", "python"], check=True, capture_output=True).stdout.decode().strip()
    )
    return Params(
        mode=mode,
        targets=targets,
        update_pins=args.update_pins,
        json=args.json,
        rebuild=args.rebuild,
        unannotated=args.unannotated,
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
    env_path_specs: List[EnvPathSpec] = []
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
    env_path_map: Dict[str, List[str]] = {}
    for path in paths:
        if os.path.isdir(path) or os.path.splitext(path)[1] in [".py", ".pyi"]:
            try:
                env = next(
                    (
                        env_path_spec["env"]
                        for env_path_spec in env_path_specs
                        if match_path(path, env_path_spec)
                    )
                )
            except StopIteration:
                raise Exception(f"Could not find environment that matched path: {path}.")
            env_path_map.setdefault(env, []).append(path)
    return env_path_map


def normalize_env(env: str, rebuild: bool, update_pins: bool, venv_python: str) -> None:
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
                        "-r",
                        dest_requirements_path,
                        # editable-mode=compat ensures dagster-internal editable installs are done
                        # in a way that is legible to pyright (i.e. not using import hooks). See:
                        #  https://github.com/microsoft/pyright/blob/main/docs/import-resolution.md#editable-installs
                        "--config-settings",
                        "editable-mode=compat",
                        *extra_pip_install_args,
                    ]
                ),
            ]
        )
        try:
            print(f"Copying {src_requirements_path} to {dest_requirements_path}....")
            shutil.copyfile(src_requirements_path, dest_requirements_path)
            subprocess.run(build_venv_cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            subprocess.run(f"rm -rf {venv_path}", shell=True, check=True)
            print(f"Partially built virtualenv for pyright environment {env} deleted.")
            raise e
        finally:
            os.remove(dest_requirements_path)

        if update_pins:
            update_pinned_requirements(env)

    return None


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
    is_internal = not os.path.exists("python_modules/dagster")
    oss_root_ref = "${DAGSTER_GIT_REPO_DIR}/" if is_internal else ""
    resolved_oss_root = os.environ["DAGSTER_GIT_REPO_DIR"].rstrip("/")
    resolved_internal_root = os.environ["DAGSTER_INTERNAL_GIT_REPO_DIR"].rstrip("/")
    dep_list = re.sub(f"-e file://{resolved_oss_root}/(.+)", f"-e {oss_root_ref}\\1", raw_dep_list)
    dep_list = re.sub(f"-e file://{resolved_internal_root}/(.+)", "-e \\1", dep_list)
    with open(get_env_path(env, "requirements-pinned.txt"), "w") as f:
        f.write(dep_list)


def run_pyright(
    env: str,
    paths: Optional[Sequence[str]],
    rebuild: bool,
    unannotated: bool,
    pinned_deps: bool,
    venv_python: str,
) -> RunResult:
    with temp_pyright_config_file(env, unannotated) as config_path:
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
            output = result.stdout == "" and result.stderr or result.stdout
            raise Exception(f"Pyright output was not valid JSON. Output was:\n\n{output}")
    return {
        "returncode": result.returncode,
        "output": cast(PyrightOutput, json_result),
    }


@contextmanager
def temp_pyright_config_file(env: str, unannotated: bool) -> Iterator[str]:
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        toml = tomli.loads(f.read())
    config = toml["tool"]["pyright"]
    config["venvPath"] = f"{PYRIGHT_ENV_ROOT}/{env}"
    include_path = get_env_path(env, "include.txt")
    exclude_path = get_env_path(env, "exclude.txt")
    config["include"] = load_path_file(include_path)
    if os.path.exists(exclude_path):
        config["exclude"] += load_path_file(exclude_path)
    config["analyzeUnannotatedFunctions"] = unannotated
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
    with open(dagster_setup, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search('"pyright==([^"]+)"', content)
    assert m is not None, "Could not find pyright version in python_modules/dagster/setup.py"
    return m.group(1)


def get_hints(output: PyrightOutput) -> Sequence[str]:
    hints: List[str] = []

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
    assert os.path.exists(".git"), "Must be run from the root of the repository"
    args = parser.parse_args()
    params = get_params(args)
    if params["mode"] == "path":
        env_path_map = map_paths_to_envs(params["targets"])
    else:
        env_path_map = {env: None for env in params["targets"]}

    for env in env_path_map:
        normalize_env(env, params["rebuild"], params["update_pins"], params["venv_python"])
    if params["skip_typecheck"]:
        print("Successfully built environments. Skipping typecheck.")
    if not params["skip_typecheck"]:
        run_results = [
            run_pyright(
                env,
                paths=env_path_map[env],
                rebuild=params["rebuild"],
                unannotated=params["unannotated"],
                pinned_deps=params["update_pins"],
                venv_python=params["venv_python"],
            )
            for env in env_path_map
        ]
        merged_result = reduce(merge_pyright_results, run_results)
        print_output(merged_result, params["json"])
        sys.exit(merged_result["returncode"])
