from collections import namedtuple
import os
import re

import click

from dagster import check
from dagster.cli.dynamic_loader import (
    repository_target_argument,
    load_target_info_from_cli_args,
    RepositoryTargetInfo,
    create_repository_loading_mode_data,
    load_yaml_from_path,
    ModuleTargetFunction,
    InvalidRepositoryLoadingComboError,
)


def get_module_target_function(info):
    check.inst_param(info, 'info', RepositoryTargetInfo)
    if info.repository_yaml:
        mode_data = create_repository_loading_mode_data(info)
        file_path = mode_data.data
        check.str_param(file_path, 'file_path')
        config = load_yaml_from_path(file_path)
        repository_config = check.dict_elem(config, 'repository')
        module_name = check.opt_str_elem(repository_config, 'module')
        fn_name = check.str_elem(repository_config, 'fn')
        if module_name:
            return ModuleTargetFunction(module_name=module_name, fn_name=fn_name)
        return None
    elif info.module_name and info.fn_name:
        return ModuleTargetFunction(module_name=info.module_name, fn_name=info.fn_name)
    elif info.python_file and info.fn_name:
        return None
    else:
        raise InvalidRepositoryLoadingComboError()


def get_notebook_scaffolding(register_repo_info):
    check.str_param(register_repo_info.import_statement, 'register_repo_info.import_statement')
    check.str_param(
        register_repo_info.declaration_statement, 'register_repo_info.declaration_statement'
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
        "import dagstermill as dm\\n",
        "{import_statement}\\n",
        "{declaration_statement}"
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
        "dm_context = dm.define_context()"
    ]
    }}
    ],
    "metadata": {{
    "celltoolbar": "Tags"
    }},
    "nbformat": 4,
    "nbformat_minor": 2
    }}'''
    return starting_notebook_init.format(
        import_statement=register_repo_info.import_statement,
        declaration_statement=register_repo_info.declaration_statement,
    )


@click.command(name='create-notebook', help=('Creates new dagstermill notebook.'))
@repository_target_argument
@click.option('--notebook', '-note', type=click.STRING, help="Name of notebook")
@click.option(
    '--solid-name',
    '-s',
    default="",
    type=click.STRING,
    help=(
        'Name of solid that represents notebook in the repository. '
        'If empty, defaults to notebook name.'
    ),
)
@click.option(
    '--force-overwrite',
    is_flag=True,
    help="Will force overwrite any existing notebook or file with the same name.",
)
def create_notebook(notebook, solid_name, force_overwrite, **kwargs):
    execute_create_notebook(notebook, solid_name, force_overwrite, **kwargs)


def execute_create_notebook(notebook, solid_name, force_overwrite, **kwargs):
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

    if not force_overwrite and os.path.isfile(notebook_path):
        click.confirm(
            (
                'Warning, {notebook_path} already exists and continuing '
                'will overwrite the existing notebook. '
                'Are you sure you want to continue?'
            ).format(notebook_path=notebook_path),
            abort=True,
        )

    if not solid_name:
        solid_name = os.path.basename(notebook_path).split(".")[0]

    repository_target_info = load_target_info_from_cli_args(kwargs)
    module_target_info = get_module_target_function(repository_target_info)

    if module_target_info:
        module = module_target_info.module_name
        fn_name = module_target_info.fn_name
        RegisterRepoInfo = namedtuple('RegisterRepoInfo', 'import_statement declaration_statement')
        register_repo_info = RegisterRepoInfo(
            "from {module} import {fn_name}".format(module=module, fn_name=fn_name),
            "dm.declare_as_solid({fn_name}(), '{solid_name}')".format(
                fn_name=fn_name, solid_name=solid_name
            ),
        )
    else:
        raise click.UsageError(
            "Cannot instantiate notebook with repository definition given by a function from a file"
        )

    with open(notebook_path, 'w') as f:
        f.write(get_notebook_scaffolding(register_repo_info))
        click.echo("Created new dagstermill notebook at {path}".format(path=notebook_path))


def create_dagstermill_cli():
    group = click.Group(name="create-notebook")
    group.add_command(create_notebook)
    return group


def main():
    cli = create_dagstermill_cli()
    # click magic
    cli(obj={})  # pylint:disable=E1120
