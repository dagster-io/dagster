from collections import namedtuple
import copy
import os
import re

import click
from papermill.iorw import load_notebook_node, write_ipynb
import nbformat

from dagster import check
from dagster.cli.dynamic_loader import (
    repository_target_argument,
    load_target_info_from_cli_args,
    RepositoryTargetInfo,
    entrypoint_from_module_target,
    load_yaml_from_path,
    InvalidRepositoryLoadingComboError,
)
from dagster.utils import safe_isfile


def get_acceptable_entrypoint(repo_target_info):
    check.inst_param(repo_target_info, 'repo_target_info', RepositoryTargetInfo)
    if repo_target_info.repository_yaml:
        check.str_param(repo_target_info.repository_yaml, 'repository_yaml')
        config = load_yaml_from_path(repo_target_info.repository_yaml)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.opt_str_elem(repository_config, 'module')
        fn_name = check.str_elem(repository_config, 'fn')
        if module_name:
            return entrypoint_from_module_target(module_name, fn_name)
        return None
    elif repo_target_info.module_name and repo_target_info.fn_name:
        return entrypoint_from_module_target(repo_target_info.module_name, repo_target_info.fn_name)
    elif repo_target_info.python_file and repo_target_info.fn_name:
        return None
    else:
        raise InvalidRepositoryLoadingComboError()


def get_notebook_scaffolding(register_repo_info):
    if register_repo_info is None:  # do not register repo
        first_cell_source = '"import dagstermill as dm"'
    else:
        check.str_param(register_repo_info.import_statement, 'register_repo_info.import_statement')
        check.str_param(
            register_repo_info.declaration_statement, 'register_repo_info.declaration_statement'
        )
        first_cell_source = '''"import dagstermill as dm\\n",
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
        "context = dm.get_context()"
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

    cell_source = 'import dagstermill as dm\n{import_statement}\n{declaration_statement}'.format(
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
    def all_none(kwargs):
        for value in kwargs.values():
            if value is not None:
                return False
        return True

    scaffolding_with_repo = True
    if all_none(cli_args):
        if os.path.exists(os.path.join(os.getcwd(), 'repository.yml')):
            cli_args['repository_yaml'] = 'repository.yml'
        elif allow_none:  # register_repo_info can remain None
            scaffolding_with_repo = False

    register_repo_info = None
    if scaffolding_with_repo:
        repository_target_info = load_target_info_from_cli_args(cli_args)
        entrypoint = get_acceptable_entrypoint(repository_target_info)

        if entrypoint:
            module = entrypoint.module_name
            fn_name = entrypoint.fn_name
            RegisterRepoInfo = namedtuple(
                'RegisterRepoInfo', 'import_statement declaration_statement'
            )
            register_repo_info = RegisterRepoInfo(
                "from {module} import {fn_name}".format(module=module, fn_name=fn_name),
                "dm.register_repository({fn_name}())".format(fn_name=fn_name),
            )
        else:
            raise click.UsageError(
                "Cannot instantiate notebook with repository definition given by a function from a file"
            )
    return register_repo_info


def execute_create_notebook(notebook, force_overwrite, **kwargs):
    if not re.match(r'^[a-zA-Z0-9\-_\\/]+$', notebook):
        raise click.BadOptionUsage(
            notebook,
            (
                'Notebook name {name} is not valid, '
                'cannot contain anything except alphanumeric characters, '
                '-, _, \\ and / for path manipulation'
            ).format(name=notebook),
        )

    notebook_path = os.path.join(
        os.getcwd(), notebook if notebook.endswith('.ipynb') else notebook + ".ipynb"
    )

    notebook_dir = os.path.dirname(notebook_path)
    if not os.path.exists(notebook_dir):
        os.makedirs(notebook_dir)

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
