import os

from automation.images import (
    aws_coverage_image,
    ensure_aws_login,
    get_aws_account_id,
    local_coverage_image,
)

from dagster import check


def image_push():
    ensure_aws_login()
    aws_image = aws_coverage_image(get_aws_account_id())
    check.invariant(
        os.system(
            'docker tag {local_image} {aws_image}'.format(
                local_image=local_coverage_image(), aws_image=aws_image,
            )
        )
        == 0
    )
    check.invariant(os.system('docker push {aws_image}'.format(aws_image=aws_image)) == 0)


if __name__ == '__main__':
    image_push()
