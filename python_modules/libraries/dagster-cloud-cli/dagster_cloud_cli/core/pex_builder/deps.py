# Build deps.pex, given a project root

import enum
import hashlib
import importlib.metadata
import json
import logging
import os
import os.path
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional

import click
from dagster_shared.utils import find_uv_workspace_root
from packaging import version

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ImportError:
    # Python < 3.11 fallback
    import tomli as tomllib

from dagster_cloud_cli import ui
from dagster_cloud_cli.core import docker_runner
from dagster_cloud_cli.core.pex_builder import util


class BuildMethod(enum.Enum):
    # try current environment, if build fails, try in a docker builder
    DOCKER_FALLBACK = "docker-fallback"
    LOCAL = "local"  # try local environment only
    DOCKER = "docker"  # try docker builder only


@dataclass(frozen=True)
class DepsRequirements:
    requirements_txt: str
    python_version: version.Version
    pex_flags: list[str]

    @property
    def hash(self) -> str:
        # The hash uniquely identifies the list of requirements used to build a deps.pex.
        # This is used as part of the cache key to reuse a cached deps.pex.
        # Note requirements_txt may have floating dependencies, so this is not perfect and may
        # reuse deps.pex even if a new PyPI package is published for a dependency.
        # An easy workaround is to pin the dependency in setup.py.
        normalized_pex_flags = sorted(set(self.pex_flags) - {"--resolve-local-platforms"})
        return hashlib.sha1(
            (
                repr(self.requirements_txt) + str(self.python_version) + repr(normalized_pex_flags)
            ).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class LocalPackages:
    local_package_paths: list[str]


def local_path_for(line: str, relative_to: str) -> Optional[str]:
    # Return the abspath for a local package, iff this line points to a local package,
    # otherwise return None.
    # This handles relative or absolute paths specified in requirements.txt,
    # eg "../some/other/dir" or "./subdir/" or "/abs/dir". For these directories we
    # include the local package as part of the source pex.
    # The "file://" urls (direct references) are correctly handled by the underlying pex build
    # anyway and do not need special treatment here.

    # Use a very specific match here to avoid accidentally matching URLs or other lines with slashes
    path = None
    if line.startswith("./") or line.startswith("../") or line.startswith("/"):
        path = os.path.abspath(os.path.join(relative_to, line.strip()))

    if path:
        if not os.path.exists(path):
            raise ValueError(
                f"Could not find local directory {path!r} referenced in requirement {line!r}"
            )

        return path

    return None


def get_requirements_lines(local_dir, python_interpreter: str) -> list[str]:
    # Combine dependencies specified in requirements.txt, setup.py, and pyproject.toml

    lines = get_requirements_txt_deps(local_dir)
    lines.extend(get_setup_py_deps(local_dir, python_interpreter))
    lines.extend(get_pyproject_toml_deps(local_dir))
    return lines


def collect_requirements(code_directory, python_interpreter: str) -> tuple[list[str], list[str]]:
    if not os.path.exists(code_directory):
        raise Exception(
            f"Specified a build directory that does not exist: {os.path.abspath(code_directory)}."
        )

    required_files = [
        "setup.py",
        "requirements.txt",
        "pyproject.toml",
    ]

    if not any(os.path.exists(os.path.join(code_directory, file)) for file in required_files):
        raise Exception(
            f"Could not find a setup.py, requirements.txt, or pyproject.toml in build directory {os.path.abspath(code_directory)}."
        )

    # traverse all local packages and return the list of local packages and other requirements
    pending = [os.path.abspath(code_directory)]  # local packages to be processed
    seen = set()

    local_package_paths = []
    deps_lines = []

    while pending:
        local_dir = pending.pop()
        if local_dir in seen:
            continue
        seen.add(local_dir)

        lines = get_requirements_lines(local_dir, python_interpreter)
        # Separate out the local packages from other requirements
        for line in lines:
            local_package_path = local_path_for(line, relative_to=local_dir)
            if local_package_path:
                if local_package_path not in local_package_paths:
                    local_package_paths.append(local_package_path)
                    pending.append(local_package_path)
            else:
                deps_lines.append(line)

    return local_package_paths, deps_lines


def get_deps_requirements(
    code_directory, python_version: version.Version
) -> tuple[LocalPackages, DepsRequirements]:
    python_interpreter = util.python_interpreter_for(python_version)

    ui.print(f"Finding dependencies using build directory {os.path.abspath(code_directory)}")

    local_package_paths, deps_lines = collect_requirements(code_directory, python_interpreter)

    deps_requirements_text = "\n".join(
        sorted(set(deps_lines)) + [""]
    )  # empty string adds trailing newline

    ui.print(f"List of local packages: {local_package_paths}")
    ui.print(f"List of dependencies: {deps_requirements_text}")

    local_packages = LocalPackages(local_package_paths=local_package_paths)
    deps_requirements = DepsRequirements(
        requirements_txt=deps_requirements_text,
        python_version=python_version,
        pex_flags=util.get_pex_flags(python_version, build_sdists=True),
    )
    ui.print(f"deps_requirements_hash: {deps_requirements.hash}")

    return local_packages, deps_requirements


def build_deps_pex(code_directory, output_directory, python_version) -> tuple[str, str]:
    _, requirements = get_deps_requirements(code_directory, python_version)
    return build_deps_from_requirements(
        requirements, output_directory, build_method=BuildMethod.DOCKER_FALLBACK
    )


# Resolving dependencies can be flaky - depends on the version of pip and the resolver algorithm.
# These flags allow trying multiple ways of building the deps.
# This also allows us to try new flags safely, by having automatic fallback.
TRY_FLAGS = [
    ["--resolver-version=pip-2020-resolver"],  # new resolver as recommended by pex team
    # disabled but left here for easy revert
    # [],  # default set of flags defined in util.py
]


class DepsBuildFailure(Exception):
    def __init__(self, proc: subprocess.CompletedProcess):
        self.proc = proc
        self.stdout = proc.stdout.decode("utf-8")
        self.stderr = proc.stderr.decode("utf-8")
        lines = self.stdout.splitlines() + self.stderr.splitlines()
        self.dependency_failure_lines = [
            line
            for line in lines
            if "No matching distribution" in line
            or "ResolutionImpossible" in line
            or "No pre-built wheel was available" in line
        ]

    def format_error(self) -> str:
        lines = []
        lines.append("Dependency build failure details:\n")
        lines.append("Command:\n" + util.indent(" ".join(self.proc.args)))
        if self.stdout:
            lines.append("\nOutput:\n" + util.indent(self.stdout))
        if self.stderr:
            lines.append("\nError:\n" + util.indent(self.stderr))
        return "".join(lines)


def build_deps_from_requirements(
    requirements: DepsRequirements,
    output_directory: str,
    build_method: BuildMethod,
) -> tuple[str, str]:
    os.makedirs(output_directory, exist_ok=True)
    deps_requirements_filename = f"deps-requirements-{requirements.hash}.txt"
    deps_requirements_path = os.path.join(output_directory, deps_requirements_filename)
    tmp_pex_filename = f"deps-from-{requirements.hash}.pex"
    tmp_pex_path = os.path.join(output_directory, tmp_pex_filename)

    with open(deps_requirements_path, "w", encoding="utf-8") as deps_requirements_file:
        deps_requirements_file.write(requirements.requirements_txt)

    ui.print(
        f"Building project dependencies for Python {requirements.python_version}, "
        f"writing to {output_directory}",
    )

    def build_in_docker() -> None:
        proc = docker_runner.run_dagster_cloud(
            map_folders={"/output": output_directory},
            run_args=[
                "serverless",
                "build-python-deps",
                f"/output/{deps_requirements_filename}",
                f"/output/{tmp_pex_filename}",
                json.dumps(requirements.pex_flags),
            ],
            env={"PEX_VERBOSE": None},  # pass through this env, if set
        )
        if proc.returncode:
            ui.error("Failed to build dependencies using docker")
            if proc.stdout:
                ui.error(proc.stdout.decode("utf-8"))
            if proc.stderr:
                ui.error(proc.stderr.decode("utf-8"))
            sys.exit(1)

    if build_method in [BuildMethod.DOCKER_FALLBACK, BuildMethod.LOCAL]:
        try:
            build_deps_from_requirements_file(
                deps_requirements_path,
                output_pex_path=tmp_pex_path,
                pex_flags=requirements.pex_flags,
            )
        except DepsBuildFailure as err:
            if build_method == BuildMethod.DOCKER_FALLBACK and err.dependency_failure_lines:
                ui.warn(
                    "Failed to build dependencies in current environment:"
                    f"{''.join(err.dependency_failure_lines)}"
                )
                ui.warn("Falling back to build in a docker environment")
                build_in_docker()
            else:
                raise ui.error("Failed to build dependencies:\n" + err.format_error())
    else:
        ui.print("Building project dependencies in a docker build environment")
        build_in_docker()

    pex_info = util.get_pex_info(tmp_pex_path)
    pex_hash = pex_info["pex_hash"]
    final_pex_path = os.path.join(output_directory, f"deps-{pex_hash}.pex")
    os.rename(tmp_pex_path, final_pex_path)
    ui.print(f"Wrote deps pex: {final_pex_path}")

    distribution_names = pex_info["distributions"].keys()
    # the distributions are named something like 'dagster-1.0.14-py3-none-any.whl'
    # and 'dagster_cloud-1.1.7-py3-none-any.whl'
    dep_names = ["dagster", "dagster_cloud"]
    dep_versions = {}
    for name in distribution_names:
        for dep_name in dep_names:
            pattern = re.compile(f"{dep_name}-(.+?)-py")
            match = pattern.match(name)
            if match:
                dep_versions[dep_name] = match.group(1)
                break

    for dep_name in dep_names:
        if dep_name not in dep_versions:
            raise ValueError(f"The {dep_name} package dependency was expected but not found.")

    return final_pex_path, dep_versions["dagster"]


def build_deps_from_requirements_file(
    deps_requirements_path: str,
    output_pex_path: str,
    pex_flags: list[str],
) -> None:
    """Attempts to build a pex file from a requirements file and raises DepsBuildFailure on failure."""
    # We try different sets of build flags and use the first one that works
    try_flags = TRY_FLAGS.copy()
    while try_flags:
        add_on_flags = try_flags.pop(0)
        pex_flags = pex_flags + add_on_flags
        logging.debug(f"Running pex with {' '.join(pex_flags)}")
        proc = util.build_pex(
            sources_directories=[],
            requirements_filepaths=[deps_requirements_path],
            pex_flags=pex_flags,
            output_pex_path=output_pex_path,
        )
        if proc.returncode:
            if try_flags:
                ui.warn(proc.stderr.decode("utf-8"))
                ui.warn("Will retry building deps with a different resolution mechanism")
            else:
                raise DepsBuildFailure(proc)
        else:
            break


def get_requirements_txt_deps(code_directory: str) -> list[str]:
    requirements_path = os.path.join(code_directory, "requirements.txt")
    if not os.path.exists(requirements_path):
        return []

    # combine multi-line strings into a single string
    combined_lines = []
    current_line = ""

    with open(requirements_path, encoding="utf-8") as file:
        for line in file:
            stripped_line = line.rstrip()
            if stripped_line.endswith("\\"):
                current_line += stripped_line[:-1]
            else:
                current_line += stripped_line
                combined_lines.append(current_line)
                current_line = ""

    # Add any remaining content if the last line ends with a backslash
    if current_line:
        combined_lines.append(current_line)

    lines = []
    for raw_line in combined_lines:
        # https://pip.pypa.io/en/stable/reference/requirements-file-format/#comments
        line = re.sub(r"(^#|\s#).*", "", raw_line)
        line = line.strip()
        # remove current dir from the deps
        if line in {"", "."}:
            continue
        lines.append(line)

    return lines


def get_setup_py_deps(code_directory: str, python_interpreter: str) -> list[str]:
    setup_py_path = os.path.join(code_directory, "setup.py")
    if not os.path.exists(setup_py_path):
        return []

    lines = []
    # write out egg_info files and load as distribution
    with tempfile.TemporaryDirectory() as temp_dir:
        proc = subprocess.run(
            [python_interpreter, setup_py_path, "egg_info", f"--egg-base={temp_dir}"],
            capture_output=True,
            check=False,
            cwd=code_directory,
        )
        if proc.returncode:
            raise ValueError(
                "Error running setup.py egg_info: "
                + proc.stdout.decode("utf-8")
                + proc.stderr.decode("utf-8")
            )
        dists = list(importlib.metadata.distributions(path=[temp_dir]))
        if len(dists) != 1:
            raise ValueError(f"Could not find distribution for {setup_py_path}")
        dist = dists[0]
        for requirement in dist.requires or []:
            lines.append(requirement)

    return lines


def _resolve_uv_workspace_dep(dep_name: str, code_directory: str) -> Optional[str]:
    """Find the relative path to a uv workspace member by package name.

    Returns a relative path like "../shared-lib" or None if not found.
    Assumes the directory name matches the package name.
    """
    result = find_uv_workspace_root(code_directory)
    if not result:
        return None

    workspace_root, _ = result
    candidate = os.path.join(str(workspace_root), dep_name)
    if os.path.isdir(candidate):
        return os.path.relpath(candidate, code_directory)

    return None


def get_pyproject_toml_deps(code_directory: str) -> list[str]:
    pyproject_path = os.path.join(code_directory, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        return []

    try:
        with open(pyproject_path, "rb") as file:
            pyproject_data = tomllib.load(file)
    except Exception as e:
        raise ValueError(f"Error parsing pyproject.toml: {e}")

    lines = []

    # Handle dependencies in [project] section (PEP 621)
    project_section = pyproject_data.get("project", {})
    dependencies = project_section.get("dependencies", [])
    for dep in dependencies:
        lines.append(str(dep))

    # Handle optional dependencies in [project.optional-dependencies]
    optional_deps = project_section.get("optional-dependencies", {})
    for group_deps in optional_deps.values():
        for dep in group_deps:
            lines.append(str(dep))

    # Handle legacy [tool.poetry.dependencies] for Poetry projects
    poetry_section = pyproject_data.get("tool", {}).get("poetry", {})
    poetry_deps = poetry_section.get("dependencies", {})
    for dep_name, dep_spec in poetry_deps.items():
        if dep_name == "python":
            continue  # Skip python version constraint

        if isinstance(dep_spec, str):
            lines.append(f"{dep_name}{dep_spec}")
        elif isinstance(dep_spec, dict):
            version_spec = dep_spec.get("version", "")
            if version_spec:
                lines.append(f"{dep_name}{version_spec}")
            else:
                # Handle complex dependency specs (git, path, etc.)
                lines.append(dep_name)

    # Handle legacy [tool.poetry.dev-dependencies] (older Poetry format)
    poetry_dev_deps = poetry_section.get("dev-dependencies", {})
    for dep_name, dep_spec in poetry_dev_deps.items():
        if isinstance(dep_spec, str):
            lines.append(f"{dep_name}{dep_spec}")
        elif isinstance(dep_spec, dict):
            version_spec = dep_spec.get("version", "")
            if version_spec:
                lines.append(f"{dep_name}{version_spec}")
            else:
                lines.append(dep_name)

    # Handle [tool.uv.sources] - resolve workspace and path dependencies to local paths
    uv_sources = pyproject_data.get("tool", {}).get("uv", {}).get("sources", {})
    if uv_sources:
        resolved_lines = []
        for line in lines:
            source_config = uv_sources.get(line)
            if source_config:
                if source_config.get("workspace"):
                    resolved_path = _resolve_uv_workspace_dep(line, code_directory)
                    if resolved_path:
                        resolved_lines.append(resolved_path)
                        continue
                elif "path" in source_config:
                    resolved_lines.append(source_config["path"])
                    continue
            resolved_lines.append(line)
        return resolved_lines

    return lines


@click.command()
@click.argument("project_dir", type=click.Path(exists=True))
@click.argument("build_output_dir", type=click.Path(exists=False))
@util.python_version_option()
def deps_main(project_dir, build_output_dir, python_version):
    deps_pex_path, dagster_version = build_deps_pex(
        project_dir, build_output_dir, util.parse_python_version(python_version)
    )


if __name__ == "__main__":
    deps_main()
