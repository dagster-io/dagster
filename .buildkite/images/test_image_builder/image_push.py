import os

from automation.images import (
    aws_test_builder_image,
    ensure_aws_login,
    get_aws_account_id,
    local_test_builder_image,
)

from dagster import check


def image_push():
    ensure_aws_login()
    aws_image = aws_test_builder_image(get_aws_account_id())
    check.invariant(
        os.system(
            'dagster tag {local_image} {aws_image}'.format(
                local_image=local_test_builder_image(), aws_image=aws_image,
            )
        )
        == 0
    )
    check.invariant(
        os.system(
            'docker push {aws_image}'.format(aws_image=aws_test_builder_image(get_aws_account_id()))
        )
        == 0
    )
