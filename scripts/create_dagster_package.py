# ruff: noqa: T201
import os

import click
from jinja2 import Environment, FileSystemLoader


def _make_dagster_package(package_name: str):
    if not package_name.startswith("dagster-"):
        print("Package name must start with 'dagster-'. Examples: dagster-snowflake, dagster-dbt.")
        return

    dagster_repo = os.getenv("DAGSTER_GIT_REPO_DIR")
    if dagster_repo is None:
        print("Must have DAGSTER_GIT_REPO_DIR set.")
        return

    package_name_underscore = package_name.replace("-", "_")
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
        ".coveragerc": {
            "path": os.path.join(package_path, ".coveragerc"),
            "has_todos": False,
            "kwargs": {},
        },
        "LICENSE": {
            "path": os.path.join(package_path, "LICENSE"),
            "has_todos": False,
            "kwargs": {},
        },
        "MANIFEST.in": {
            "path": os.path.join(package_path, "MANIFEST.in"),
            "has_todos": False,
            "kwargs": {"underscore_name": package_name_underscore},
        },
        "README.md": {
            "path": os.path.join(package_path, "README.md"),
            "has_todos": False,
            "kwargs": {"hyphen_name": package_name},
        },
        "setup.cfg": {
            "path": os.path.join(package_path, "setup.cfg"),
            "has_todos": False,
            "kwargs": {"underscore_name": package_name_underscore},
        },
        "setup.py": {
            "path": os.path.join(package_path, "setup.py"),
            "has_todos": True,
            "kwargs": {
                "underscore_name": package_name_underscore,
                "hyphen_name": package_name,
            },
        },
        "tox.ini": {
            "path": os.path.join(package_path, "tox.ini"),
            "has_todos": True,
            "kwargs": {
                "underscore_name": package_name_underscore,
                "hyphen_name": package_name,
            },
        },
        "py.typed": {"path": os.path.join(src_path, "py.typed"), "has_todos": False, "kwargs": {}},
        "version.py": {
            "path": os.path.join(src_path, "version.py"),
            "has_todos": False,
            "kwargs": {},
        },
        "test_version.py": {
            "path": os.path.join(tests_path, "test_version.py"),
            "has_todos": False,
            "kwargs": {
                "underscore_name": package_name_underscore,
            },
        },
        "__init__.py": {
            "path": os.path.join(src_path, "__init__.py"),
            "has_todos": False,
            "kwargs": {
                "hyphen_name": package_name,
            },
        },
    }

    has_todos = []

    for to_create, vars in files_to_create.items():
        print(f"Writing {to_create}")
        template = jinja_env.get_template(f"{to_create}.tmpl")
        with open(vars["path"], "w") as f:
            template.stream(**vars["kwargs"]).dump(f)

        if vars["has_todos"]:
            has_todos.append(vars["path"])

    # test __init__.py
    path = os.path.join(tests_path, "__init__.py")
    print(f"Writing {path}")
    with open(path, "w"):
        pass

    # API docs
    docs_path = os.path.join(
        dagster_repo, f"docs/sphinx/sections/api/apidocs/libraries/{package_name}.rst"
    )
    formal_name = " ".join(
        [word.capitalize() for word in package_name.split("dagster-")[1].split("-")]
    )
    template = jinja_env.get_template("api-docs.rst.tmpl")
    print(f"Writing {docs_path}")
    with open(docs_path, "w") as f:
        template.stream(
            hyphen_name=package_name,
            underscore_name=package_name_underscore,
            formal_name=formal_name,
        ).dump(f)

    has_todos.append(docs_path)

    # finish up

    has_todos_string = "\n".join(has_todos)
    print(
        f"\n{package_name} has been created! See the TODOs in the following files to finish"
        f" setup:\n{has_todos_string}"
    )


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
