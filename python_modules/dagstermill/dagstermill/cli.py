import copy
import os

import click
import nbformat
from papermill.iorw import load_notebook_node, write_ipynb

from dagster.utils import mkdir_p, safe_isfile


def get_notebook_scaffolding():
    first_cell_source = '"import dagstermill"'

    starting_notebook_init = '''
    {{
    "cells": [
    {{
    "cell_type": "code",
    "execution_count": null,
    "metadata": {{}},
    "outputs": [],
    "source": [
        {first_cell_source}
    ]
    }},
    {{
    "cell_type": "code",
    "execution_count": null,
    "metadata": {{
        "tags": [
        "parameters"
        ]
    }},
    "outputs": [],
    "source": [
        "context = dagstermill.get_context()"
    ]
    }}
    ],
    "metadata": {{
    "celltoolbar": "Tags"
    }},
    "nbformat": 4,
    "nbformat_minor": 2
    }}'''
    return starting_notebook_init.format(first_cell_source=first_cell_source)


@click.command(name='register-notebook', help=('Registers repository in existing notebook'))
@click.option('--notebook', '-note', type=click.Path(exists=True), help='Path to notebook')
def retroactively_scaffold_notebook(notebook):
    execute_retroactive_scaffold(notebook)


def execute_retroactive_scaffold(notebook_path):
    nb = load_notebook_node(notebook_path)
    new_nb = copy.deepcopy(nb)

    import_cell_source = 'import dagstermill'
    import_cell = nbformat.v4.new_code_cell(source=import_cell_source)

    parameters_cell_source = 'context = dagstermill.get_context()'
    parameters_cell = nbformat.v4.new_code_cell(source=parameters_cell_source)
    parameters_cell.metadata['tags'] = ['parameters']

    new_nb.cells = [import_cell, parameters_cell] + nb.cells
    write_ipynb(new_nb, notebook_path)


@click.command(name='create-notebook', help=('Creates new dagstermill notebook.'))
@click.option('--notebook', '-note', type=click.Path(), help="Name of notebook")
@click.option(
    '--force-overwrite',
    is_flag=True,
    help="Will force overwrite any existing notebook or file with the same name.",
)
def create_notebook(notebook, force_overwrite):
    execute_create_notebook(notebook, force_overwrite)


def execute_create_notebook(notebook, force_overwrite):
    notebook_path = os.path.join(
        os.getcwd(), notebook if notebook.endswith('.ipynb') else notebook + ".ipynb"
    )

    notebook_dir = os.path.dirname(notebook_path)
    mkdir_p(notebook_dir)

    if not force_overwrite and safe_isfile(notebook_path):
        click.confirm(
            (
                'Warning, {notebook_path} already exists and continuing '
                'will overwrite the existing notebook. '
                'Are you sure you want to continue?'
            ).format(notebook_path=notebook_path),
            abort=True,
        )

    with open(notebook_path, 'w') as f:
        f.write(get_notebook_scaffolding())
        click.echo("Created new dagstermill notebook at {path}".format(path=notebook_path))


def create_dagstermill_cli():
    group = click.Group(name="dagstermill")
    group.add_command(create_notebook)
    group.add_command(retroactively_scaffold_notebook)
    return group


def main():
    cli = create_dagstermill_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
