import os

import click
from automation.git import git_repo_root
from automation.images import (
    aws_integration_base_image,
    ensure_aws_login,
    execute_docker_build,
    get_aws_account_id,
    local_integration_snapshot_builder_image,
)

from dagster import check


@click.command()
@click.option('-v', '--python-version', type=click.STRING, required=True)
@click.option('-b', '--base-image-version', type=click.STRING, required=True)
def build_image(python_version, base_image_version):
    # always set cwd to the directory where the file lives
    execute_build_image(python_version, base_image_version)


def execute_build_image(python_version, base_image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(base_image_version, 'base_image_version')

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    ensure_aws_login()

    builder_image = local_integration_snapshot_builder_image(python_version, base_image_version)

    docker_args = {
        'BASE_IMAGE': aws_integration_base_image(
            get_aws_account_id(), python_version, base_image_version
        ),
    }

    execute_docker_build(image=builder_image, docker_args=docker_args)

    root = git_repo_root()

    target_reqs_path = os.path.join(
        root,
        '.buildkite',
        'images',
        'integration',
        'snapshot-reqs-{python_version}.txt'.format(python_version=python_version),
    )

    # e.g.
    # docker run snapshot-builder pip freeze --exclude-editable
    check.invariant(
        os.system(
            'docker run {builder_image} pip freeze --exclude-editable > {reqs}'.format(
                builder_image=builder_image, reqs=target_reqs_path
            )
        )
        == 0
    )


if __name__ == '__main__':
    build_image()  # pylint: disable=no-value-for-parameter
