import os
import shutil
from subprocess import check_output

import click
from automation.git import git_repo_root
from automation.images import execute_docker_build, local_integration_base_image
from packaging import version

from dagster import check


def execute_build_integration_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')

    ver = version.parse(python_version)
    major, minor, _dot = ver.release

    debian_version = 'buster' if major == 3 and minor == 8 else 'stretch'

    docker_args = {
        'DEBIAN_VERSION': debian_version,
        'PYTHON_VERSION': python_version,
        'PYTHON_MAJOR_VERSION': str(major),
    }

    execute_docker_build(
        image=local_integration_base_image(
            python_version=python_version, image_version=image_version
        ),
        docker_args=docker_args,
    )


@click.command()
@click.option('-v', '--python-version', type=click.STRING, required=True)
@click.option('-i', '--image_version', type=click.STRING, required=True)
def image_build(python_version, image_version):
    execute_image_build(python_version, image_version)


def execute_image_build(python_version, image_version):
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

        execute_build_integration_image(python_version, image_version)

    finally:
        shutil.rmtree('./scala_modules')


if __name__ == '__main__':
    image_build()  # pylint: disable=no-value-for-parameter
