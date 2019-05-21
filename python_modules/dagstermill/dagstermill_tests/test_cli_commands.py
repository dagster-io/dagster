# encoding: utf-8

import os

from click.testing import CliRunner

from dagster.utils import script_relative_path
from dagstermill.cli import create_notebook

EXPECTED_OUTPUT_SHELL = '''
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
EXPECTED_IMPORT_STATEMENT = "from dagstermill.examples.repository import define_example_repository"


def check_notebook_expected_output(notebook_name, expected_output):
    with open(
        os.path.join(
            script_relative_path('.'),
            'notebooks',
            notebook_name if notebook_name.endswith(".ipynb") else notebook_name + ".ipynb",
        ),
        'r',
    ) as f:
        notebook_content = f.read()
        assert notebook_content == expected_output, notebook_content + "\n\n\n\n" + expected_output


def cleanup(notebook_name):
    notebook_path = os.path.join(
        script_relative_path("."),
        'notebooks',
        notebook_name if notebook_name.endswith(".ipynb") else notebook_name + ".ipynb",
    )
    if os.path.exists(notebook_path):
        os.remove(notebook_path)


def execute_dagstermill_cli(file_name=None, module_name=None, fn_name=None, notebook_name=None):
    runner = CliRunner()
    args = (
        []
        + (['-f', file_name] if file_name else [])
        + (['--module-name', module_name] if module_name else [])
        + (['--fn-name', fn_name] if fn_name else [])
        + (['--notebook', notebook_name] if notebook_name else [])
        + ['--force-overwrite']
    )
    return runner.invoke(create_notebook, args)


def test_module_example():
    original_cwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        execute_dagstermill_cli(
            module_name="dagster",
            fn_name="function_name",
            notebook_name="notebooks/CLI_test_module",
        )
        EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
            import_statement="from dagster import function_name",
            declaration_statement="dm.register_repository(function_name())",
        )
        check_notebook_expected_output(
            notebook_name="CLI_test_module", expected_output=EXPECTED_OUTPUT
        )
    finally:
        cleanup("CLI_test_module")
        os.chdir(original_cwd)


# These tests need to be revisited -- they definitely aren't working as written, and I think none of
# them actually work
# def test_file_example():
#     with pytest.raises(subprocess.CalledProcessError) as cpe:
#         execute_dagstermill_cli(
#             file_name="random_file.py",
#             fn_name="function_name",
#             notebook_name="notebooks/CLI_test_file",
#         )
#         assert (
#             "Cannot instantiate notebook with repository definition given by a function from a file"
#             in str(cpe.value)
#         )


def test_yaml_example():
    original_cwd = os.getcwd()
    try:
        os.chdir(script_relative_path('.'))
        execute_dagstermill_cli(notebook_name="notebooks/CLI_test_YAML")
        EXPECTED_OUTPUT = EXPECTED_OUTPUT_SHELL.format(
            import_statement=EXPECTED_IMPORT_STATEMENT,
            declaration_statement="dm.register_repository(define_example_repository())",
        )
        check_notebook_expected_output(
            notebook_name="CLI_test_YAML", expected_output=EXPECTED_OUTPUT
        )
    finally:
        cleanup("CLI_test_YAML")
        os.chdir(original_cwd)


def test_invalid_filename_example():
    execute_dagstermill_cli(
        module_name="module_name", fn_name="function_name", notebook_name="notebooks/CLI!!~@您好"
    )
