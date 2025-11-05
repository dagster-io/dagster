# Build source.pex, given a project root

import os
import os.path
import shutil
import subprocess
import tempfile
from uuid import uuid4

import click

from dagster_cloud_cli import ui
from dagster_cloud_cli.core.pex_builder import deps, util

# inspired by https://github.com/github/gitignore/blob/main/Python.gitignore
# would be nice to just read the gitignore and use that
IGNORED_PATTERNS = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".tox",
    ".nox",
    "*.pyc",
    ".mypy_cache",
    ".cache",
    ".venv",
]


def build_source_pex(
    code_directory: str, local_package_paths: list[str], output_directory, python_version
):
    output_directory = os.path.abspath(output_directory)
    os.makedirs(output_directory, exist_ok=True)
    code_directory = os.path.abspath(code_directory)
    tmp_pex_path = os.path.join(output_directory, f"source-tmp-{uuid4()}.pex")

    build_pex_using_setup_py(code_directory, local_package_paths, tmp_pex_path, python_version)

    pex_info = util.get_pex_info(tmp_pex_path)
    pex_hash = pex_info["pex_hash"]
    pex_name = f"source-{pex_hash}.pex"
    final_pex_path = os.path.join(output_directory, pex_name)
    os.rename(tmp_pex_path, final_pex_path)
    ui.print(f"Wrote source pex: {final_pex_path}")
    return final_pex_path


def _build_local_package(local_dir: str, build_dir: str, python_interpreter: str):
    if os.path.exists(os.path.join(local_dir, "setup.py")):
        ui.print(f"Building package at {local_dir!r} using {python_interpreter} setup.py build")
        command = [
            python_interpreter,
            "setup.py",
            "build",
            "--build-lib",
            build_dir,
        ]
        subprocess.run(command, check=True, cwd=local_dir)
    elif os.path.exists(os.path.join(local_dir, "pyproject.toml")):
        ui.print(f"Building package at {local_dir!r} using {python_interpreter} -m pip install")
        # Use pip install with --target to build and install the package to the build directory
        # This handles pyproject.toml files properly using modern Python build standards
        command = [
            python_interpreter,
            "-m",
            "pip",
            "install",
            "--target",
            build_dir,
            "--no-deps",  # Don't install dependencies, just the package itself
            ".",
        ]
        subprocess.run(command, check=True, cwd=local_dir)
    else:
        ui.warn(f"No setup.py or pyproject.toml found in {local_dir!r} - will not build.")


def build_pex_using_setup_py(
    code_directory: str,
    local_package_paths: list[str],
    tmp_pex_path,
    python_version,
):
    """Builds package using setup.py and copies built output into PEX."""
    python_interpreter = util.python_interpreter_for(python_version)
    with tempfile.TemporaryDirectory() as build_dir, tempfile.TemporaryDirectory() as sources_dir:
        included_dirs = [build_dir]

        for local_dir in local_package_paths:
            _build_local_package(
                local_dir=local_dir,
                build_dir=build_dir,
                python_interpreter=python_interpreter,
            )

        _build_local_package(
            local_dir=code_directory,
            build_dir=build_dir,
            python_interpreter=python_interpreter,
        )

        # We always include the code_directory source in a special package called working_directory
        ui.print(
            f"Bundling the source {code_directory} into the 'working_directory' package at {sources_dir}",
        )
        _prepare_working_directory(code_directory, sources_dir)
        included_dirs.append(sources_dir)

        # note this may include tests directories
        proc = util.build_pex(
            included_dirs,
            requirements_filepaths=[],
            pex_flags=util.get_pex_flags(python_version),
            output_pex_path=tmp_pex_path,
        )

        if proc.returncode:
            ui.error("build source pex stdout:")
            ui.error(util.indent(proc.stdout.decode("utf-8")))
            ui.error("build source pex stderr:")
            ui.error(util.indent(proc.stderr.decode("utf-8")))
            raise ui.error(
                f"Failed to package source code into a source pex, error code: {proc.returncode}"
            )
        ui.print(f"Built source pex: {tmp_pex_path}")


def _prepare_working_directory(code_directory, sources_directory):
    # Copy code_directory contents into a package called working_directory under sources_directory
    package_dir = os.path.join(sources_directory, "working_directory")
    os.makedirs(package_dir, exist_ok=True)

    with open(os.path.join(package_dir, "__init__.py"), "w", encoding="utf-8") as init_file:
        init_file.write("# Auto generated package containing the original source at root/")

    shutil.copytree(
        code_directory,
        os.path.join(package_dir, "root"),
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*IGNORED_PATTERNS),
        # We copy over symlinks as symlinks rather than try and resolve them and copy the target.
        # This prevents build failures if the target file doesn't exist locally. If the target
        # doesn't exist at runtime, this will fail and that is acceptable.
        symlinks=True,
    )


@click.command()
@click.argument("project_dir", type=click.Path(exists=True))
@click.argument("build_output_dir", type=click.Path(exists=False))
@util.python_version_option()
def source_main(project_dir, build_output_dir, python_version):
    local_packages, _ = deps.get_deps_requirements(
        code_directory=project_dir, python_version=python_version
    )
    build_source_pex(
        project_dir,
        local_packages.local_package_paths,
        build_output_dir,
        util.parse_python_version(python_version),
    )


if __name__ == "__main__":
    source_main()
