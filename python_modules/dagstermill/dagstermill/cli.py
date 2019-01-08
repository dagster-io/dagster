import os
import sys
import click        
import re

from dagster.cli.dynamic_loader import repository_target_argument, load_target_info_from_cli_args, get_module_target_function

def get_scaffolding(register_repo_str):
    STARTING_NOTEBOOK_INIT = '''
        {{
        "cells": [
        {{
        "cell_type": "code",
        "execution_count": null,
        "metadata": {{}},
        "outputs": [],
        "source": [
            "import dagstermill as dm\\n",
            "{0}\\n",
            "{1}"
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
        }}
    '''
    return STARTING_NOTEBOOK_INIT.format(register_repo_str[0], register_repo_str[1])

def create_dagstermill_cli():
    return ui

@click.command(
    name='ui',
    help=(
        'Creates new dagstermill notebook.'
    ),
)
@repository_target_argument
@click.option('--notebook', '-note', type=click.STRING, help="Name of notebook")
@click.option('--solid-name', '-s', default="", type=click.STRING, help="Name of solid that represents notebook in the repository. If empty, defaults to notebook name.")
@click.option('--jupyter', '-j', is_flag = True, help="Launches jupyter notebook and opens to newly created notebook")
def ui(notebook, solid_name, jupyter, **kwargs):
    
    #@Uma TODO: we might want to sanitize the notebook name so that it's a valid filename
    #Perhaps something like this: https://github.com/django/django/blob/master/django/utils/text.py function: get_valid_filename()

    if not notebook.endswith(".ipynb"):
        notebook += ".ipynb"
    notebook_path = os.path.join(os.getcwd(), notebook)

    if os.path.isfile(notebook_path):
        click.confirm("Warning, {notebook_path} already exists and continuing will overwrite the existing notebook. Are you sure you want to continue?".format(notebook_path=notebook_path), abort=True)

    if solid_name == "":
        solid_name = os.path.basename(notebook_path).split(".")[0]

    register_repo_str = ["#Register notebook as solid within repo",
                         "#dm.declare_as_solid(PLACEHOLDER_repository_defn_function(), '{solid_name}')".format(solid_name=solid_name)]

    repository_target_info = load_target_info_from_cli_args(kwargs)
    module_target_info = get_module_target_function(repository_target_info)

    if module_target_info:
        module = module_target_info.module_name
        fn_name = module_target_info.fn_name
        register_repo_str = ["from {module} import {fn_name}".format(module=module, fn_name=fn_name),
                            "dm.declare_as_solid({fn_name}(), '{solid_name}')".format(fn_name=fn_name, solid_name=solid_name)]

    with open(notebook_path, 'w') as f:
        f.write(get_scaffolding(register_repo_str))
        click.echo("Created new dagstermill notebook at {path}".format(path=notebook_path))
    if jupyter:
        #@Uma TODO: We should probably not be making system calls, and if we are, we should probably make sure it's from the right folder
        os.system("jupyter notebook {name}".format(name=notebook)) 