import copy
import os
import subprocess

import click
import nbformat
from dagster import check
from dagster.seven.json import loads
from dagster.utils import mkdir_p, safe_isfile
from papermill.iorw import load_notebook_node, write_ipynb


def get_import_cell():
    return nbformat.v4.new_code_cell(source="import dagstermill")


def get_parameters_cell():
    parameters_cell = nbformat.v4.new_code_cell(source="context = dagstermill.get_context()")
    parameters_cell.metadata["tags"] = ["parameters"]
    return parameters_cell


def get_kernelspec(kernel):
    kernelspecs = loads(subprocess.check_output(["jupyter", "kernelspec", "list", "--json"]))

    check.invariant(len(kernelspecs["kernelspecs"]) > 0, "No available Jupyter kernelspecs!")

    if kernel is None:
        preferred_kernels = list(
            filter(
                lambda kernel_name: kernel_name in kernelspecs["kernelspecs"],
                ["dagster", "python3", "python"],
            )
        ) + list(kernelspecs["kernelspecs"].keys())
        kernel = preferred_kernels[0]
        print(  # pylint: disable=print-call
            "No kernel specified, defaulting to '{kernel}'".format(kernel=kernel)
        )

    check.invariant(
        kernel in kernelspecs["kernelspecs"],
        "Could not find kernel '{kernel}': available kernels are [{kernels}]".format(
            kernel=kernel,
            kernels=", ".join(["'{k}'".format(k=k) for k in kernelspecs["kernelspecs"]]),
        ),
    )

    return {
        "name": kernel,
        "language": kernelspecs["kernelspecs"][kernel]["spec"]["language"],
        "display_name": kernelspecs["kernelspecs"][kernel]["spec"]["display_name"],
    }


def get_notebook_scaffolding(kernelspec):
    check.dict_param(kernelspec, "kernelspec", key_type=str, value_type=str)

    notebook = nbformat.v4.new_notebook()

    notebook.cells = [get_import_cell(), get_parameters_cell()]

    metadata = {"celltoolbar": "Tags", "kernelspec": kernelspec}

    notebook.metadata = metadata

    return nbformat.writes(notebook)


@click.command(
    name="register-notebook", help=("Scaffolds existing notebook for dagstermill compatibility")
)
@click.option("--notebook", "-note", type=click.Path(exists=True), help="Path to existing notebook")
def retroactively_scaffold_notebook(notebook):
    execute_retroactive_scaffold(notebook)


def execute_retroactive_scaffold(notebook_path):
    nb = load_notebook_node(notebook_path)
    new_nb = copy.deepcopy(nb)
    new_nb.cells = [get_import_cell(), get_parameters_cell()] + nb.cells
    write_ipynb(new_nb, notebook_path)


@click.command(name="create-notebook", help=("Creates new dagstermill notebook."))
@click.option("--notebook", "-note", type=click.Path(), help="Name of notebook")
@click.option(
    "--force-overwrite",
    is_flag=True,
    help="Will force overwrite any existing notebook or file with the same name.",
)
@click.option(
    "--kernel",
    type=click.STRING,
    help=(
        "Specify an existing Jupyter kernel to use. (Run `jupyter kernelspec list` to view "
        "available kernels.) By default a kernel called 'dagster' will be used, if available, "
        "then one called 'python3', then 'python', and then the first available kernel."
    ),
)
def create_notebook(notebook, force_overwrite, kernel):
    execute_create_notebook(notebook, force_overwrite, kernel)


def execute_create_notebook(notebook, force_overwrite, kernel):
    notebook_path = os.path.join(
        os.getcwd(), notebook if notebook.endswith(".ipynb") else notebook + ".ipynb"
    )

    notebook_dir = os.path.dirname(notebook_path)
    mkdir_p(notebook_dir)

    if not force_overwrite and safe_isfile(notebook_path):
        click.confirm(
            (
                "Warning, {notebook_path} already exists and continuing "
                "will overwrite the existing notebook. "
                "Are you sure you want to continue?"
            ).format(notebook_path=notebook_path),
            abort=True,
        )

    with open(notebook_path, "w") as f:
        f.write(get_notebook_scaffolding(get_kernelspec(kernel)))
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
