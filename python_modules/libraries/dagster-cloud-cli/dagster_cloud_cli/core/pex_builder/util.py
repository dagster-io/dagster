import json
import logging
import os
import subprocess
import sys
from subprocess import CompletedProcess
from typing import Optional
from zipfile import ZipFile

import click
from packaging import version

from dagster_cloud_cli.core.pex_builder.platforms import COMPLETE_PLATFORMS
from dagster_cloud_cli.utils import DEFAULT_PYTHON_VERSION

TARGET_PYTHON_VERSIONS = [
    version.Version(python_version) for python_version in ["3.9", "3.10", "3.11", "3.12", "3.13"]
]


def run_python_subprocess(args: list[str], env=None) -> CompletedProcess:
    """Invoke python with given args, using an environment identical to current environment."""
    # If running a pex file directly, we invoke the executable pex file again.
    # Otherwise we assume we're running in a pex generated venv and use the python executable.
    cmd = os.getenv("PEX", sys.executable)

    args = [cmd] + args
    logging.debug(f"Running {args} in {os.path.abspath(os.curdir)}")
    proc = subprocess.run(args, capture_output=True, env=env, check=False)
    return proc


def run_self_module(module_name, args: list[str], env=None) -> CompletedProcess:
    """Invoke this executable again with -m {module}."""
    return run_python_subprocess(["-m", module_name, *args], env=env)


def get_pex_flags(python_version: version.Version, build_sdists: bool = True) -> list[str]:
    """python_version should includes the major and minor version only, eg Version('3.11')."""
    if python_version not in TARGET_PYTHON_VERSIONS:
        raise ValueError(
            f"Unsupported python version {python_version}. Supported: {TARGET_PYTHON_VERSIONS}."
        )
    version_tag = f"{python_version.major}{python_version.minor}"  # eg '38'
    # Resolves dependencies using the local interpreter, effectively allowing source distributions
    # to work (since they get built by the local interpreter).
    # If build_sdists is false and a binary distribution matching the platform below is not
    # available for a dependency, then the build will fail.
    # see also https://linear.app/elementl/issue/CLOUD-2023/pex-builds-fail-for-dbt-core-dependency
    resolve_local = ["--resolve-local-platforms"] if build_sdists else []
    # This is mainly useful in local mac test environments
    include_current = ["--platform=current"] if os.getenv("PEX_INCLUDE_CURRENT_PLATFORM") else []

    complete_platform = os.getenv(
        "PEX_COMPLETE_PLATFORM", json.dumps(COMPLETE_PLATFORMS[version_tag])
    )

    return [
        # this complete platform matches what can run on our serverless base images
        f"--complete-platform={complete_platform}",
        *include_current,
        # this ensures PEX_PATH is not cleared and any subprocess invoked can also use this.
        # this is important for running console scripts that use the pex environment (eg dbt)
        "--no-strip-pex-env",
        # use the latest version of pip bundled with pex - this will typically provide
        # the best dependency resolution logic. added in
        # https://github.com/pantsbuild/pex/releases/tag/v2.1.132
        "--pip-version=latest",
        "-v",  # verbose logging, level 3
        "-v",
        "-v",
        *resolve_local,
    ]


def build_pex(
    sources_directories: list[str],
    requirements_filepaths: list[str],
    pex_flags: list[str],
    output_pex_path: str,
    pex_root: Optional[str] = None,
) -> CompletedProcess:
    """Invoke pex with common build flags and pass parameters through to specific pex flags.

    sources_directories: passed to the pex -D flag (aka --source-directories)
    requirements_filepaths: passed to the pex -r flag (aka --requirement)

    Platform:
    For the pex --platform tag used below, see pex --help and
    https://peps.python.org/pep-0425/
    https://peps.python.org/pep-0427/

    Packages for the current platform are only included if requested with PEX_INCLUDE_CURRENT_PLATFORM
    The manylinux platform ensures pexes built on local machines (macos, windows) are compatible
    with linux on cloud.

    The python_version tuple eg ('3', '9') determines the target runtime environment. In theory
    we can build a pex in an environment without the target python version present.
    """
    flags = pex_flags.copy()
    if not sources_directories and not requirements_filepaths:
        raise ValueError("At least one of sources_directories or requirements_filepath required.")
    for src_dir in sources_directories:
        flags.extend(["-D", src_dir])
    for req_file in requirements_filepaths:
        flags.extend(["-r", req_file])
    pex_args = [*flags, "-o", output_pex_path]
    if pex_root:
        pex_args.extend(["--pex-root", pex_root])
    return run_pex_command(pex_args)


def run_pex_command(args: list[str]) -> CompletedProcess:
    # https://github.com/pantsbuild/pex/issues/1969#issuecomment-1336105021
    env = {**os.environ, "_PEX_FILE_LOCK_STYLE": "bsd"}

    return run_self_module("pex", args, env=env)


def run_dagster_cloud_cli_command(args: list[str]) -> CompletedProcess:
    return run_self_module("dagster_cloud_cli.entrypoint", args)


def run_dagster_command(args: list[str]) -> CompletedProcess:
    return run_self_module("dagster", args)


def get_pex_info(pex_filepath):
    with ZipFile(pex_filepath) as pex_zip:
        return json.load(pex_zip.open("PEX-INFO"))


def build_pex_tag(filepaths: list[str]) -> str:
    return "files=" + ":".join(sorted(os.path.basename(filepath) for filepath in filepaths))


def python_interpreter_for(python_version: version.Version) -> str:
    return "python" + str(python_version)  # eg 'python3.11'


def python_version_option():
    """Reusable click.option."""
    return click.option(
        "--python-version",
        type=click.Choice([str(v) for v in TARGET_PYTHON_VERSIONS]),
        default=DEFAULT_PYTHON_VERSION,
        show_default=True,
        help="Target Python version.",
    )


def parse_python_version(python_version: str) -> version.Version:
    return version.Version(python_version)


def parse_kv(ctx, param: str, value: Optional[str]):
    if not value:
        return {}
    try:
        return dict(part.split("=", 1) for part in value.split(","))
    except ValueError as err:
        raise ValueError(f"Value {value!r} could not be parsed: {err}")


def indent(text: str, prefix="| "):
    return "".join([prefix + line for line in text.splitlines(keepends=True)])
