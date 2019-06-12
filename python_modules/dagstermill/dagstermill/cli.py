from collections import namedtuple
import copy
import os

import click
from papermill.iorw import load_notebook_node, write_ipynb
import nbformat

from dagster import check
from dagster.cli.pipeline import repository_target_argument
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.utils import all_none, DEFAULT_REPOSITORY_YAML_FILENAME, safe_isfile, mkdir_p


def get_notebook_scaffolding(register_repo_info):
    if register_repo_info is None:  # do not register repo
        first_cell_source = '"import dagstermill"'
    else:
        check.str_param(register_repo_info.import_statement, 'register_repo_info.import_statement')
        check.str_param(
            register_repo_info.declaration_statement, 'register_repo_info.declaration_statement'
        )
        first_cell_source = '''"import dagstermill\\n",
        "{import_statement}\\n",
        "{declaration_statement}"'''.format(
            import_statement=register_repo_info.import_statement,
            declaration_statement=register_repo_info.declaration_statement,
        )

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
@repository_target_argument
@click.option('--notebook', '-note', type=click.STRING, help='Path to notebook')
def retroactively_scaffold_notebook(notebook, **kwargs):
    execute_retroactive_scaffold(notebook, **kwargs)


def execute_retroactive_scaffold(notebook_path, **kwargs):
    nb = load_notebook_node(notebook_path)
    new_nb = copy.deepcopy(nb)
    register_repo_info = get_register_repo_info(kwargs, allow_none=False)

    cell_source = 'import dagstermill\n{import_statement}\n{declaration_statement}'.format(
        import_statement=register_repo_info.import_statement,
        declaration_statement=register_repo_info.declaration_statement,
    )

    newcell = nbformat.v4.new_code_cell(source=cell_source)
    newcell.metadata['tags'] = ['injected-repo-registration']
    new_nb.cells = [newcell] + nb.cells
    write_ipynb(new_nb, notebook_path)


@click.command(name='create-notebook', help=('Creates new dagstermill notebook.'))
@repository_target_argument
@click.option('--notebook', '-note', type=click.STRING, help="Name of notebook")
@click.option(
    '--force-overwrite',
    is_flag=True,
    help="Will force overwrite any existing notebook or file with the same name.",
)
def create_notebook(notebook, force_overwrite, **kwargs):
    execute_create_notebook(notebook, force_overwrite, **kwargs)


def get_register_repo_info(cli_args, allow_none=True):
    scaffolding_with_repo = True
    if all_none(cli_args):
        if os.path.exists(os.path.join(os.getcwd(), DEFAULT_REPOSITORY_YAML_FILENAME)):
            cli_args['repository_yaml'] = DEFAULT_REPOSITORY_YAML_FILENAME
        elif allow_none:  # register_repo_info can remain None
            scaffolding_with_repo = False

    if (
        cli_args['python_file']
        and cli_args['fn_name']
        and not cli_args['module_name']
        and not cli_args['repository_yaml']
    ):
        raise click.UsageError(
            "Cannot instantiate notebook with repository definition given by a "
            "function from a file"
        )

    register_repo_info = None
    if scaffolding_with_repo:
        handle = handle_for_repo_cli_args(cli_args)
        module = handle.entrypoint.module_name
        fn_name = handle.entrypoint.fn_name
        RegisterRepoInfo = namedtuple('RegisterRepoInfo', 'import_statement declaration_statement')
        register_repo_info = RegisterRepoInfo(
            "from {module} import {fn_name}".format(module=module, fn_name=fn_name),
            "dagstermill.register_repository({fn_name}())".format(fn_name=fn_name),
        )
    return register_repo_info


def execute_create_notebook(notebook, force_overwrite, **kwargs):
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
    register_repo_info = get_register_repo_info(kwargs)

    with open(notebook_path, 'w') as f:
        f.write(get_notebook_scaffolding(register_repo_info))
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
