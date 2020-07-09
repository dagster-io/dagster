import os
import shutil
from subprocess import check_output

import click
from automation.git import git_repo_root
from automation.images import (
    aws_integration_base_image,
    execute_docker_build,
    get_aws_account_id,
    local_integration_image,
)

from dagster import check


def execute_build_integration_image(python_version, image_version, base_integration_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')

    docker_args = {
        'BASE_IMAGE': aws_integration_base_image(
            get_aws_account_id(), python_version, base_integration_version
        ),
        'PYTHON_VERSION': python_version,
    }

    local_image = local_integration_image(
        python_version=python_version, image_version=image_version
    )

    execute_docker_build(local_image, docker_args)


@click.command()
@click.option('-v', '--python-version', type=click.STRING, required=True)
@click.option('-i', '--image-version', type=click.STRING, required=True)
@click.option('-b', '--base-image-version', type=click.STRING, required=True)
def build(python_version, image_version, base_image_version):
    execute_image_build(python_version, image_version, base_image_version)


def execute_image_build(python_version, image_version, base_image_version):
    root = git_repo_root()

    # always set cwd to the directory where the file lives
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    scala_modules_dir = os.path.join(root, 'scala_modules')
    try:
        rsync_args = (
            (
                "rsync -av --exclude='*target*' --exclude='*.idea*' --exclude='*.class' "
                "{scala_modules_dir} ."
            )
            .format(scala_modules_dir=scala_modules_dir)
            .split(' ')
        )
        check_output(rsync_args)

        execute_build_integration_image(python_version, image_version, base_image_version)

    finally:
        shutil.rmtree('./scala_modules')


if __name__ == '__main__':
    build()  # pylint: disable=no-value-for-parameter
