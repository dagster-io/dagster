import os

import click
from automation.images import execute_docker_build, local_unit_image, unit_base_image

from dagster import check


def execute_(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')


@click.command()
@click.option('-v', '--python-version', type=click.STRING, required=True)
@click.option('-i', '--image-version', type=click.STRING, required=True)
def build(python_version, image_version):
    execute_image_build(python_version, image_version)


def execute_image_build(python_version, image_version):
    # always set cwd to the directory where the file lives
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    docker_args = {
        'BASE_IMAGE': unit_base_image(python_version),
        'PYTHON_VERSION': python_version,
    }

    local_image = local_unit_image(python_version=python_version, image_version=image_version)

    execute_docker_build(local_image, docker_args)


if __name__ == '__main__':
    build()  # pylint: disable=no-value-for-parameter
