# encoding: utf-8

import contextlib
import json
import os
import re
import sys

import pytest
from click.testing import CliRunner
from dagster.check import CheckError
from dagster.utils import file_relative_path, pushd
from dagstermill.cli import create_notebook, retroactively_scaffold_notebook

EXPECTED_OUTPUT = """{{
 "cells": [
  {{
   "cell_type": "code",
   "execution_count": null,
   "metadata": {{}},
   "outputs": [],
   "source": [
    "import dagstermill"
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
  "celltoolbar": "Tags",
  "kernelspec": {{
   "display_name": "dagster",
   "language": "python",
   "name": "dagster"
  }}
 }},
 "nbformat": 4,
 "nbformat_minor": {minor_version}
}}""".format(
    minor_version=("4" if sys.version_info.major >= 3 else "2")
)

EXPECTED_IMPORT_STATEMENT = "from dagstermill.examples.repository import define_example_repository"


def check_notebook_expected_output(notebook_path, expected_output):
    with open(notebook_path, "r") as f:
        notebook_content = f.read()
        assert notebook_content == expected_output, notebook_content + "\n\n\n\n" + expected_output


@contextlib.contextmanager
def scaffold(notebook_name=None, kernel=None):
    runner = CliRunner()
    args_ = (
        []
        + (["--notebook", notebook_name] if notebook_name else [])
        + ["--force-overwrite"]
        + (["--kernel", kernel] if kernel else [])
    )

    res = runner.invoke(create_notebook, args_)
    if res.exception:
        raise res.exception
    assert res.exit_code == 0

    yield os.path.abspath(notebook_name)

    if os.path.exists(notebook_name):
        os.unlink(notebook_name)

    if os.path.exists(notebook_name + ".ipynb"):
        os.unlink(notebook_name + ".ipynb")


def test_scaffold():
    with pushd(file_relative_path(__file__, ".")):
        with scaffold(notebook_name="notebooks/cli_test_scaffold") as notebook_path:
            check_notebook_expected_output(
                notebook_path + ".ipynb", expected_output=EXPECTED_OUTPUT
            )

        with scaffold(
            notebook_name="notebooks/cli_test_scaffold", kernel="dagster"
        ) as notebook_path:
            check_notebook_expected_output(
                notebook_path + ".ipynb", expected_output=EXPECTED_OUTPUT
            )

        with pytest.raises(
            CheckError, match=re.escape("Could not find kernel 'foobar': available kernels are")
        ):
            with scaffold(notebook_name="notebooks/cli_test_scaffold", kernel="foobar") as _:
                pass


def test_invalid_filename_example():
    if sys.version_info > (3,):
        with scaffold(notebook_name="notebooks/CLI!!~@您好") as _notebook_name:
            assert True
    else:
        with scaffold(notebook_name="notebooks/CLI!! ~@") as _notebook_name:
            assert True


def test_retroactive_scaffold():
    notebook_path = file_relative_path(__file__, "notebooks/retroactive.ipynb")
    with open(notebook_path, "r") as fd:
        retroactive_notebook = fd.read()
    try:
        runner = CliRunner()
        args = ["--notebook", notebook_path]
        runner.invoke(retroactively_scaffold_notebook, args)
        with open(notebook_path, "r") as fd:
            scaffolded = json.loads(fd.read())
            assert [
                x
                for x in scaffolded["cells"]
                if "parameters" in x.get("metadata", {}).get("tags", [])
            ]
    finally:
        with open(notebook_path, "w") as fd:
            fd.write(retroactive_notebook)


def test_double_scaffold():
    try:
        notebook_path = file_relative_path(__file__, "notebooks/overwrite.ipynb")
        with open(notebook_path, "w") as fd:
            fd.write("print('Hello, world!')")

        runner = CliRunner()
        args = ["--notebook", notebook_path]
        res = runner.invoke(create_notebook, args)

        assert isinstance(res.exception, SystemExit)
        assert res.exception.code == 1
        assert "already exists and continuing will overwrite the existing notebook." in res.output
    finally:
        if os.path.exists(notebook_path):
            os.unlink(notebook_path)
