import os

import click
from automation.images import (
    aws_integration_image,
    ensure_aws_login,
    get_aws_account_id,
    local_integration_image,
)

from dagster import check


@click.command()
@click.option('-v', '--python-version', type=click.STRING, required=True)
@click.option('-i', '--image_version', type=click.STRING, required=True)
def image_push(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    check.invariant(os.environ.get('AWS_ACCOUNT_ID'), 'must have AWS_ACCOUNT_ID set')

    # always set cwd to the directory where the file lives
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    aws_image = aws_integration_image(
        aws_account_id=get_aws_account_id(),
        python_version=python_version,
        image_version=image_version,
    )

    ensure_aws_login()

    check.invariant(
        os.system(
            'docker tag {local_image} {aws_image}'.format(
                local_image=local_integration_image(python_version, image_version),
                aws_image=aws_image,
            )
        )
        == 0,
        'docker tag command must succeed',
    )

    check.invariant(
        os.system('docker push {aws_image}'.format(aws_image=aws_image)) == 0,
        'docker push must succeed',
    )


if __name__ == '__main__':
    image_push()  # pylint: disable=no-value-for-parameter
