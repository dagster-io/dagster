#!/usr/bin/env python3

"""Tools to manage tagging and publishing releases of the Dagster projects.

Please follow the checklist in RELEASING.md at the root of this repository.

For detailed usage instructions, please consult the command line help,
available by running `python publish.py --help`.
"""

import os
import subprocess
import sys
import tempfile
import urllib

import click
import packaging.version
import requests
import slack
import virtualenv
from automation.git import (
    get_git_repo_branch,
    get_most_recent_git_tag,
    git_check_status,
    git_commit_updates,
    git_push,
    git_repo_root,
    git_user,
    set_git_tag,
)
from automation.utils import which_

from dagster import check

from .dagster_module_publisher import DagsterModulePublisher
from .pypirc import ConfigFileError, RCParser
from .utils import format_module_versions

CLI_HELP = """Tools to help tag and publish releases of the Dagster projects.

By convention, these projects live in a single monorepo, and the submodules are versioned in
lockstep to avoid confusion, i.e., if dagster is at 0.3.0, dagit is also expected to be at
0.3.0.

Versions are tracked in the version.py files present in each submodule and in the git tags
applied to the repository as a whole. These tools help ensure that these versions do not drift.
"""


PYPIRC_EXCEPTION_MESSAGE = """You must have credentials available to PyPI in the form of a
~/.pypirc file (see: https://docs.python.org/2/distutils/packageindex.html#pypirc):

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>
"""


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option("--autoclean", is_flag=True)
@click.option("--dry-run", is_flag=True)
def publish(autoclean, dry_run):
    """Publishes (uploads) all submodules to PyPI.

    Appropriate credentials must be available to twine, e.g. in a ~/.pypirc file, and users must
    be permissioned as maintainers on the PyPI projects. Publishing will fail if versions (git
    tags and Python versions) are not in lockstep, if the current commit is not tagged, or if
    there are untracked changes.
    """
    assert os.getenv("SLACK_RELEASE_BOT_TOKEN"), "No SLACK_RELEASE_BOT_TOKEN env variable found."

    try:
        RCParser.from_file()
    except ConfigFileError:
        raise ConfigFileError(PYPIRC_EXCEPTION_MESSAGE)

    assert "\nwheel" in subprocess.check_output(["pip", "list"]).decode("utf-8"), (
        "You must have wheel installed in order to build packages for release -- run "
        "`pip install wheel`."
    )

    assert which_("twine"), (
        "You must have twine installed in order to upload packages to PyPI -- run "
        "`pip install twine`."
    )

    assert which_("yarn"), (
        "You must have yarn installed in order to build dagit for release -- see "
        "https://yarnpkg.com/lang/en/docs/install/"
    )
    dmp = DagsterModulePublisher()

    checked_version = dmp.check_version()
    click.echo("... and match git tag on most recent commit...")
    git_check_status()
    click.echo("... and that there is no cruft present...")
    dmp.check_for_cruft(autoclean)
    click.echo("... and that the directories look like we expect")
    dmp.check_directory_structure()

    click.echo("Publishing packages to PyPI...")

    dmp.publish_all(dry_run=dry_run)

    parsed_version = packaging.version.parse(checked_version)
    if not parsed_version.is_prerelease and not dry_run:
        slack_client = slack.WebClient(os.environ["SLACK_RELEASE_BOT_TOKEN"])
        slack_client.chat_postMessage(
            channel="#general",
            text=("{git_user} just published a new version: {version}.").format(
                git_user=git_user(), version=checked_version
            ),
        )


@cli.command()
@click.argument("ver")
@click.option("--dry-run", is_flag=True)
def release(ver, dry_run):
    """Tags all submodules for a new release.

    Ensures that git tags, as well as the version.py files in each submodule, agree and that the
    new version is strictly greater than the current version. Will fail if the new version
    is not an increment (following PEP 440). Creates a new git tag and commit.
    """
    dmp = DagsterModulePublisher()
    dmp.check_new_version(ver)
    dmp.set_version_info(new_version=ver, dry_run=dry_run)
    dmp.commit_new_version(ver, dry_run=dry_run)
    set_git_tag(ver, dry_run=dry_run)
    click.echo(
        "Successfully set new version and created git tag {version}. You may continue with the "
        "release checklist.".format(version=ver)
    )


@cli.command()
def version():
    """Gets the most recent tagged version."""
    dmp = DagsterModulePublisher()

    module_versions = dmp.check_all_versions_equal()
    git_tag = get_most_recent_git_tag()
    parsed_version = packaging.version.parse(git_tag)
    errors = {}
    for module_name, module_version in module_versions.items():
        if packaging.version.parse(module_version["__version__"]) > parsed_version:
            errors[module_name] = module_version["__version__"]
    if errors:
        click.echo(
            "Warning: Found modules with existing versions that did not match the most recent "
            "tagged version {git_tag}:\n{versions}".format(
                git_tag=git_tag, versions=format_module_versions(module_versions)
            )
        )
    else:
        click.echo(
            "All modules in lockstep with most recent tagged version: {git_tag}".format(
                git_tag=git_tag
            )
        )


@cli.command()
@click.argument("version")
def audit(version):  # pylint: disable=redefined-outer-name
    """Checks that the given version is installable from PyPI in a new virtualenv."""
    dmp = DagsterModulePublisher()

    for module in dmp.all_publishable_modules:
        res = requests.get(
            urllib.parse.urlunparse(
                ("https", "pypi.org", "/".join(["pypi", module.name, "json"]), None, None, None)
            )
        )
        module_json = res.json()
        assert (
            version in module_json["releases"]
        ), "Version not available for module {module_name}, expected {expected}, released version is {received}".format(
            module_name=module, expected=version, received=module_json["info"]["version"]
        )

    bootstrap_text = """
def after_install(options, home_dir):
    for module_name in [{module_names}]:
        subprocess.check_output([
            os.path.join(home_dir, 'bin', 'pip'), 'install', '{{module}}=={version}'.format(
                module=module_name
            )
        ])

""".format(
        module_names=", ".join(
            [
                "'{module_name}'".format(module_name=module.name)
                for module in dmp.all_publishable_modules
            ]
        ),
        version=version,
    )

    bootstrap_script = virtualenv.create_bootstrap_script(bootstrap_text)

    with tempfile.TemporaryDirectory() as venv_dir:
        with tempfile.NamedTemporaryFile("w") as bootstrap_script_file:
            bootstrap_script_file.write(bootstrap_script)

            args = [sys.executable, bootstrap_script_file.name, venv_dir]

            click.echo(subprocess.check_output(args).decode("utf-8"))


@cli.command()
@click.option("--helm-repo", "-r", required=True)
@click.option("--ver", "-v", required=True)
@click.option("--dry-run", is_flag=True)
def helm(helm_repo, ver, dry_run):
    """Publish the Dagster Helm chart

    See: https://medium.com/containerum/how-to-make-and-share-your-own-helm-package-50ae40f6c221
    for more info on this process
    """

    helm_path = os.path.join(git_repo_root(), "helm")

    check.invariant(
        get_git_repo_branch(helm_repo) == "gh-pages", "helm repo must be on gh-pages branch"
    )

    cmd = [
        "helm",
        "package",
        "dagster",
        "-d",
        helm_repo,
        "--app-version",
        ver,
        "--version",
        ver,
    ]
    click.echo(click.style("Running command: " + " ".join(cmd) + "\n", fg="green"))
    click.echo(subprocess.check_output(cmd, cwd=helm_path))

    cmd = ["helm", "repo", "index", ".", "--url", "https://dagster-io.github.io/helm/"]
    click.echo(click.style("Running command: " + " ".join(cmd) + "\n", fg="green"))
    click.echo(subprocess.check_output(cmd, cwd=helm_repo))

    # Commit and push Helm updates for this Dagster release
    msg = "Helm release for Dagster release {}".format(ver)
    git_commit_updates(helm_repo, msg)
    git_push(cwd=helm_repo, dry_run=dry_run)


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
