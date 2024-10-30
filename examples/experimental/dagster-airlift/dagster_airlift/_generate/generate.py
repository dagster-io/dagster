import os
from enum import Enum
from pathlib import Path
from typing import Optional

import click
import jinja2

TUTORIAL_MAIN_DIR = Path(__file__).parent / "templates" / "tutorial"
TUTORIAL_PATH = Path(__file__).parent / "templates" / "tutorial" / "common"
TOP_LEVEL_PACKAGE_NAME_PLACEHOLDER = "TOP_LEVEL_PACKAGE_NAME_PLACEHOLDER"
PACKAGE_NAME_PLACEHOLDER = "PACKAGE_NAME_PLACEHOLDER"


class Stage(Enum):
    initial = "initial"
    peer = "peer"
    observe = "observe"
    migrate = "migrate"
    complete = "complete"

    @property
    def is_airflow_migrated(self) -> bool:
        return self in {Stage.migrate, Stage.complete}


def get_path_to_module(dst_dir: Path, module_prefix: str) -> Path:
    return (
        dst_dir
        / f"{module_prefix.lower().replace('_', '-')}-tutorial"
        / f"{module_prefix}_tutorial"
    )


def get_definitions_file_path(dst_dir: Path, module_prefix: str) -> Path:
    return get_path_to_module(dst_dir, module_prefix) / "dagster_defs" / "definitions.py"


def get_shared_folder_path(dst_dir: Path, module_prefix: str) -> Path:
    return get_path_to_module(dst_dir, module_prefix) / "shared"


def get_airflow_dags_folder_path(dst_dir: Path, module_prefix: str) -> Path:
    return get_path_to_module(dst_dir, module_prefix) / "airflow_dags"


def get_definitions_file_for_stage(stage: Stage) -> Path:
    return TUTORIAL_MAIN_DIR / "stages" / f"{stage.value}.py.tmpl"


def get_shared_artifacts_for_stage(stage: Stage) -> Optional[Path]:
    return TUTORIAL_MAIN_DIR / "shared_impl" if stage.is_airflow_migrated else None


def get_airflow_dag_code_for_stage(stage: Stage) -> Path:
    return (
        TUTORIAL_MAIN_DIR
        / "airflow_dags"
        / ("migrated" if stage.is_airflow_migrated else "unmigrated")
    )


def add_additional_files_for_stage(
    stage: Stage, env: jinja2.Environment, module_prefix: str, dst_dir: Path
) -> None:
    defs_template_file = get_definitions_file_for_stage(stage)
    with open(get_definitions_file_path(dst_dir, module_prefix), "w", encoding="utf8") as f:
        f.write(
            fill_jinja_template(
                path_to_template=defs_template_file, env=env, module_prefix=module_prefix
            )
        )
    shared_artifacts_dir = get_shared_artifacts_for_stage(stage)
    if shared_artifacts_dir:
        dst_dir = get_shared_folder_path(dst_dir, module_prefix)
        for file in shared_artifacts_dir.iterdir():
            copy_file(file, dst_dir / file.name)

    airflow_dag_code_path = get_airflow_dag_code_for_stage(stage)
    airflow_dags_folder_path = get_airflow_dags_folder_path(dst_dir, module_prefix)
    for file in airflow_dag_code_path.iterdir():
        airflow_dags_folder_path.mkdir(parents=True, exist_ok=True)
        dst_file = airflow_dags_folder_path / file.name
        with open(dst_file, "w", encoding="utf8") as f:
            f.write(
                fill_jinja_template(path_to_template=file, env=env, module_prefix=module_prefix)
            )


def generate_tutorial(path: Path, module_prefix: str, stage: Stage) -> None:
    """Generate the tutorial example at a given directory."""
    click.echo(f"Creating an airlift tutorial project at {path}.")
    normalized_tutorial_name = f"{module_prefix.lower().replace('_', '-')}-tutorial"
    normalized_package_name = f"{module_prefix}_tutorial"
    full_path = path / normalized_tutorial_name
    normalized_path = os.path.normpath(full_path)
    os.mkdir(normalized_path)

    loader = jinja2.FileSystemLoader(searchpath=TUTORIAL_MAIN_DIR)
    env = jinja2.Environment(loader=loader)
    for root, dirs, files in os.walk(TUTORIAL_PATH):
        # For each subdirectory in the source template, create a subdirectory in the destination.
        for dirname in dirs:
            src_dir_path = os.path.join(root, dirname)
            src_relative_dir_path = os.path.relpath(src_dir_path, TUTORIAL_PATH)
            dst_relative_dir_path = src_relative_dir_path.replace(
                PACKAGE_NAME_PLACEHOLDER,
                f"{module_prefix}_tutorial",
                1,
            )
            dst_dir_path = os.path.join(normalized_path, dst_relative_dir_path)

            os.mkdir(dst_dir_path)

        # For each file in the source template, render a file in the destination.
        for filename in files:
            src_file_path = os.path.join(root, filename)
            src_relative_file_path = os.path.relpath(src_file_path, TUTORIAL_PATH)
            dst_relative_file_path = src_relative_file_path.replace(
                PACKAGE_NAME_PLACEHOLDER,
                normalized_package_name,
                1,
            )
            dst_file_path = os.path.join(normalized_path, dst_relative_file_path)

            if dst_file_path.endswith(".tmpl"):
                dst_file_path = dst_file_path[: -len(".tmpl")]

                with open(dst_file_path, "w", encoding="utf8") as f:
                    f.write(
                        fill_jinja_template(
                            path_to_template=Path(src_file_path),
                            env=env,
                            module_prefix=module_prefix,
                        )
                    )
                    f.write("\n")
            else:
                copy_file(Path(src_file_path), Path(dst_file_path))

    add_additional_files_for_stage(stage, env, module_prefix, path)

    click.echo(f"Generated files for airlift project in {path}.")


def fill_jinja_template(path_to_template: Path, env: jinja2.Environment, module_prefix: str) -> str:
    template = env.get_template(name=path_to_template.relative_to(TUTORIAL_MAIN_DIR).as_posix())
    return template.render(
        TOP_LEVEL_PACKAGE_NAME_PLACEHOLDER=f"{module_prefix.lower().replace('_', '-')}-tutorial",
        PACKAGE_NAME_PLACEHOLDER=f"{module_prefix}_tutorial",
        ALL_CAPS_PACKAGE_NAME_PLACEHOLDER=f"{module_prefix.upper()}_TUTORIAL",
    )


def copy_file(src: Path, dst: Path) -> None:
    with open(src, "rb") as f:
        with open(dst, "wb") as out:
            out.write(f.read())
