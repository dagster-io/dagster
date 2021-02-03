# pylint: disable=print-call
import json
import os
import shutil

import click
from automation.git import get_most_recent_git_tag

from .utils import copy_directory

EXAMPLES_JSON_PATH = "docs/next/src/pages/examples/examples.json"

# Location of the template assets used here
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")

CLI_HELP = """This CLI is used for generating new skeleton examples or libraries with all of the
necessary files like tox.ini, etc.
"""


def add_to_examples_json(name):
    with open(EXAMPLES_JSON_PATH, "r") as examples_file:
        examples = json.load(examples_file)

    if name in {example["name"] for example in examples}:
        raise click.UsageError(
            "Example with name {name} already exists in {path}".format(
                name=name, path=EXAMPLES_JSON_PATH
            )
        )

    examples.append({"name": name, "title": "", "description": ""})

    with open(EXAMPLES_JSON_PATH, "w") as examples_file:
        json.dump(examples, examples_file, indent=4)


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option(
    "--name", prompt='Name of library (ex: "foo" will create dagster-foo)', help="Name of library"
)
def library(name):
    """Scaffolds a Dagster library <NAME> in python_modules/libraries/dagster-<NAME>."""
    template_library_path = os.path.join(ASSETS_PATH, "dagster-library-tmpl")
    new_template_library_path = os.path.abspath(
        "python_modules/libraries/dagster-{name}".format(name=name)
    )

    if os.path.exists(new_template_library_path):
        raise click.UsageError("Library with name {name} already exists".format(name=name))

    copy_directory(template_library_path, new_template_library_path)

    version = get_most_recent_git_tag()

    for dname, _, files in os.walk(new_template_library_path):
        new_dname = dname.replace("library-tmpl", name)

        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                s = f.read()
            s = s.replace("{{LIBRARY_NAME}}", name)
            s = s.replace("{{VERSION}}", version)
            with open(fpath, "w") as f:
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
    template_library_path = os.path.join(ASSETS_PATH, "dagster-example-tmpl")
    new_template_library_path = os.path.abspath("examples/{name}".format(name=name))
    doc_path = os.path.abspath("./docs/next/src/pages/examples/{name}.mdx".format(name=name))

    if os.path.exists(new_template_library_path):
        raise click.UsageError("Example with name {name} already exists".format(name=name))

    if os.path.exists(doc_path):
        raise click.UsageError("Docs page already exists: {doc_path}".format(doc_path=doc_path))

    add_to_examples_json(name)

    copy_directory(template_library_path, new_template_library_path)

    version = get_most_recent_git_tag()

    for dname, _, files in os.walk(new_template_library_path):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                s = f.read()
            s = s.replace("{{EXAMPLE_NAME}}", name)
            s = s.replace("{{VERSION}}", version)
            with open(fpath, "w") as f:
                f.write(s)

            new_fname = fname.replace(".tmpl", "").replace("{{EXAMPLE_NAME}}", name)
            new_fpath = os.path.join(dname, new_fname)
            shutil.move(fpath, new_fpath)
            print("Created {path}".format(path=new_fpath))

        new_dname = dname.replace("example-tmpl", name)
        shutil.move(dname, new_dname)

    shutil.move(os.path.join(new_template_library_path, "README.mdx"), doc_path)

    print("Example created at {path}".format(path=new_template_library_path))
    print("Documentation stub created at {path}".format(path=doc_path))
    print("Added metadata to {path}".format(path=EXAMPLES_JSON_PATH))


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
