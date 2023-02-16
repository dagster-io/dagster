import os

import click
from jinja2 import Environment, FileSystemLoader


def _make_dagster_package(package_name: str):
    package_name_underscore = package_name.replace("-", "_")
    dagster_repo = os.getenv("DAGSTER_GIT_REPO_DIR")
    if dagster_repo is None:
        print("Must have DAGSTER_GIT_REPO_DIR set.")
        return

    libraries_path = os.path.join(dagster_repo, "python_modules/libraries")
    package_path = os.path.join(libraries_path, package_name)
    src_path = os.path.join(package_path, package_name_underscore)
    tests_path = os.path.join(package_path, package_name_underscore + "_tests")

    print(f"Making directory {src_path}")
    os.makedirs(src_path)
    print(f"Making directory {tests_path}")
    os.makedirs(tests_path)

    templates_path = os.path.join(dagster_repo, "scripts/templates_create_dagster_package")
    jinja_env = Environment(loader=FileSystemLoader(templates_path))

    files_to_create = {
        ".coveragerc": {"path": os.path.join(package_path, ".coveragerc"), "kwargs": {}},
        "LICENSE": {"path": os.path.join(package_path, "LICENSE"), "kwargs": {}},
        "MANIFEST.in": {
            "path": os.path.join(package_path, "MANIFEST.in"),
            "kwargs": {"underscore_name": package_name_underscore},
        },
        "README.md": {
            "path": os.path.join(package_path, "README.md"),
            "kwargs": {"hyphen_name": package_name},
        },
        "setup.cfg": {
            "path": os.path.join(package_path, "setup.cfg"),
            "kwargs": {"underscore_name": package_name_underscore},
        },
        "setup.py": {
            "path": os.path.join(package_path, "setup.py"),
            "kwargs": {
                "underscore_name": package_name_underscore,
                "hyphen_name": package_name,
            },
        },
        "tox.ini": {
            "path": os.path.join(package_path, "tox.ini"),
            "kwargs": {
                "underscore_name": package_name_underscore,
                "hyphen_name": package_name,
            },
        },
        "py.typed": {"path": os.path.join(src_path, "py.typed"), "kwargs": {}},
        "version.py": {"path": os.path.join(src_path, "version.py"), "kwargs": {}},
    }

    for to_create, vars in files_to_create.items():
        print(f"Writing {to_create}")
        template = jinja_env.get_template(to_create)
        with open(vars["path"], "w+") as f:
            template.stream(**vars["kwargs"]).dump(f)


@click.command()
@click.option(
    "--name",
    "-n",
    help="The top-level name of the package to create. Example: dagster-snowflake, dagster-dbt.",
    type=click.STRING,
    required=True,
)
def create_dagster_package(name):
    print(f"Creating package {name}")
    _make_dagster_package(name)


if __name__ == "__main__":
    create_dagster_package()
