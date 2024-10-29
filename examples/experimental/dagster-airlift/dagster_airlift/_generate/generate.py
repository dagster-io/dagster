import os
import posixpath
from pathlib import Path

import click
import jinja2

TUTORIAL_PATH = Path(__file__).parent / "templates" / "tutorial-example"
TOP_LEVEL_PACKAGE_NAME_PLACEHOLDER = "TOP_LEVEL_PACKAGE_NAME_PLACEHOLDER"
PACKAGE_NAME_PLACEHOLDER = "PACKAGE_NAME_PLACEHOLDER"


def generate_tutorial(path: Path, module_prefix: str) -> None:
    """Generate the tutorial example at a given directory."""
    click.echo(f"Creating an airlift tutorial project at {path}.")
    normalized_tutorial_name = f"{module_prefix.lower().replace('_', '-')}-tutorial"
    normalized_package_name = f"{module_prefix}_tutorial"
    full_path = path / normalized_tutorial_name
    normalized_path = os.path.normpath(full_path)
    os.mkdir(normalized_path)

    loader = jinja2.FileSystemLoader(searchpath=TUTORIAL_PATH)
    env = jinja2.Environment(loader=loader)
    top_level_module_prefix = "-".join(module_prefix.split("_")).lower()
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
                    # Jinja template names must use the POSIX path separator "/".
                    template_name = src_relative_file_path.replace(os.sep, posixpath.sep)
                    template = env.get_template(name=template_name)
                    f.write(
                        template.render(
                            TOP_LEVEL_PACKAGE_NAME_PLACEHOLDER=f"{top_level_module_prefix}-tutorial",
                            PACKAGE_NAME_PLACEHOLDER=f"{module_prefix}_tutorial",
                            ALL_CAPS_PACKAGE_NAME_PLACEHOLDER=f"{module_prefix.upper()}_TUTORIAL",
                        )
                    )
                    f.write("\n")
            else:
                with open(dst_file_path, "wb") as f:
                    with open(src_file_path, "rb") as src_f:
                        f.write(src_f.read())

    click.echo(f"Generated files for airlift project in {path}.")
