# pylint: disable=print-call
import os
import shutil
from contextlib import contextmanager

import click
from automation.git import get_most_recent_git_tag

from .utils import copy_directory

# Location of the template assets used here
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")

CLI_HELP = """This CLI is used for generating new skeleton examples or libraries with all of the
necessary files like tox.ini, etc.
"""


@contextmanager
def git_root_as_cwd():
    origin = os.getcwd()
    git_root = origin
    while not os.path.exists(f"{git_root}/.git") and not git_root == "/":
        git_root = os.path.dirname(git_root)
    if git_root == "/":
        raise Exception("Not in the dagster git repository. Exiting.")
    os.chdir(git_root)
    yield
    os.chdir(origin)


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option(
    "--name", prompt='Name of library (ex: "foo" will create dagster-foo)', help="Name of library"
)
def library(name: str):
    """Scaffolds a Dagster library <NAME> in python_modules/libraries/dagster-<NAME>."""

    with git_root_as_cwd():
        template_library_path = os.path.join(ASSETS_PATH, "dagster-library-tmpl")
        new_template_library_path = os.path.abspath(f"python_modules/libraries/dagster-{name}")

        if os.path.exists(new_template_library_path):
            raise click.UsageError(f"Library with name {name} already exists")

        copy_directory(template_library_path, new_template_library_path)

        version = get_most_recent_git_tag()

        for dname, _, files in os.walk(new_template_library_path):
            new_dname = dname.replace("library-tmpl", name)

            for fname in files:
                fpath = os.path.join(dname, fname)
                with open(fpath, encoding="utf8") as f:
                    s = f.read()
                s = s.replace("{{LIBRARY_NAME}}", name)
                s = s.replace("{{VERSION}}", version)
                with open(fpath, "w", encoding="utf8") as f:
                    f.write(s)

                new_fname = fname.replace(".tmpl", "")
                new_fpath = os.path.join(dname, new_fname)

                shutil.move(fpath, new_fpath)
                print("Created {path}".format(path=os.path.join(new_dname, new_fname)))

            shutil.move(dname, new_dname)

        print("Library created at {path}".format(path=new_template_library_path))


@cli.command()
@click.option("--name", prompt="Name of example to create", help="Name of example")
def example(name):
    """Scaffolds a Dagster example in the top-level examples/ folder."""

    with git_root_as_cwd():
        template_library_path = os.path.join(ASSETS_PATH, "dagster-example-tmpl")
        new_template_example_path = os.path.abspath("examples/{name}".format(name=name))

        if os.path.exists(new_template_example_path):
            raise click.UsageError("Example with name {name} already exists".format(name=name))

        copy_directory(template_library_path, new_template_example_path)

        version = get_most_recent_git_tag()

        for dname, _, files in os.walk(new_template_example_path):
            for fname in files:
                fpath = os.path.join(dname, fname)
                with open(fpath, encoding="utf8") as f:
                    s = f.read()
                s = s.replace("{{EXAMPLE_NAME}}", name)
                s = s.replace("{{VERSION}}", version)
                with open(fpath, "w", encoding="utf8") as f:
                    f.write(s)

                new_fname = fname.replace(".tmpl", "").replace("{{EXAMPLE_NAME}}", name)
                new_fpath = os.path.join(dname, new_fname)
                shutil.move(fpath, new_fpath)
                print("Created {path}".format(path=new_fpath))

            new_dname = dname.replace("example-tmpl", name)
            shutil.move(dname, new_dname)

        print("Example created at {path}".format(path=new_template_example_path))


def main() -> None:
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
