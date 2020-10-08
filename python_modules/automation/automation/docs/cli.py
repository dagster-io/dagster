import os
import shutil

import click

from .check_library_docs import validate_library_readmes
from .repo import DagsterDocsRepo, DagsterRepo

CLI_HELP = """This CLI is used for validating and updating Dagster docs.
"""
DEFAULT_DOCS_DIR = "/tmp/dagster-docs"


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option("-v", "--docs-version", type=click.STRING, required=True)
@click.option("-d", "--docs-dir", type=click.STRING, required=False, default=DEFAULT_DOCS_DIR)
def build(docs_version, docs_dir):
    ddr = DagsterDocsRepo(docs_dir)
    dr = DagsterRepo()

    ddr.check_new_version_dir(docs_version)
    ddr.remove_existing_docs_files()

    # Build and copy new docs files into dagster-docs
    dr.build_docs(docs_version)
    copytree(dr.out_path, docs_dir)

    dr.commit(docs_version)
    ddr.commit(docs_version)


@cli.command()
def validate_libraries():
    validate_library_readmes()


def copytree(src, dst):
    """https://stackoverflow.com/a/12514470/11295366"""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
