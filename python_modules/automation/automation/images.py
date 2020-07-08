import os

from dagster import check


def get_aws_account_id():
    check.invariant(os.environ.get('AWS_ACCOUNT_ID'), 'must have AWS_ACCOUNT_ID set')
    return os.environ.get('AWS_ACCOUNT_ID')


def aws_image(aws_account_id, image):
    check.str_param(aws_account_id, 'aws_account_id')
    check.str_param(image, 'image')
    return "{aws_account_id}.dkr.ecr.us-west-1.amazonaws.com/{image}".format(
        aws_account_id=aws_account_id, image=image
    )


def aws_integration_image(aws_account_id, python_version, image_version):
    check.str_param(aws_account_id, 'aws_account_id')
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return aws_image(aws_account_id, integration_image(python_version, image_version))


def aws_integration_base_image(aws_account_id, python_version, image_version):
    check.str_param(aws_account_id, 'aws_account_id')
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return aws_image(aws_account_id, integration_base_image(python_version, image_version))


def integration_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'buildkite-integration:py{python_version}-{image_version}'.format(
        python_version=python_version, image_version=image_version
    )


def integration_base_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'buildkite-integration-base:py{python_version}-{image_version}'.format(
        python_version=python_version, image_version=image_version
    )


def integration_snapshot_builder_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'buildkite-integration-snapshot-builder:py{python_version}-{image_version}'.format(
        python_version=python_version, image_version=image_version
    )


def local_integration_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'dagster/{image}'.format(image=integration_image(python_version, image_version))


def local_integration_base_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'dagster/{image}'.format(image=integration_base_image(python_version, image_version))


def local_integration_snapshot_builder_image(python_version, image_version):
    check.str_param(python_version, 'python_version')
    check.str_param(image_version, 'image_version')
    return 'dagster/{image}'.format(
        image=integration_snapshot_builder_image(python_version, image_version)
    )


def ensure_aws_login():
    check.invariant(
        os.system('aws ecr get-login --no-include-email --region us-west-1 | sh') == 0,
        'aws command must succeed',
    )


def local_test_builder_image():
    return 'dagster/test-image-builder:v2'


def aws_test_builder_image(aws_account_id):
    check.str_param(aws_account_id, 'aws_account_id')
    return "{aws_account_id}.dkr.ecr.us-west-1.amazonaws.com/test-image-builder:v2".format(
        aws_account_id=aws_account_id
    )


def execute_docker_build(image, docker_args=None):
    check.str_param(image, 'image')
    docker_args = check.opt_dict_param(docker_args, 'docker_args', key_type=str, value_type=str)

    args = ['docker', 'build', '.']

    for arg, value in docker_args.items():
        args.append('--build-arg')
        args.append('{arg}={value}'.format(arg=arg, value=value))

    args.append('-t')
    args.append(image)

    # os.system passes through stdout in a streaming way which I what I want here
    retval = os.system(' '.join(args))
    check.invariant(retval == 0, 'Process must exist successfully')


def execute_docker_push(local_image, remote_image):
    check.str_param(local_image, 'local_image')
    check.str_param(remote_image, 'remote_image')

    ensure_aws_login()

    check.invariant(
        os.system(
            'docker tag {local_image} {remote_image}'.format(
                local_image=local_image, remote_image=remote_image,
            )
        )
        == 0,
        'docker tag command must succeed',
    )

    check.invariant(
        os.system('docker push {remote_image}'.format(remote_image=remote_image)) == 0,
        'docker push must succeed',
    )


def local_coverage_image():
    return 'dagster/coverage-image:v1'


def aws_coverage_image(aws_account_id):
    check.str_param(aws_account_id, 'aws_account_id')
    return "{aws_account_id}.dkr.ecr.us-west-1.amazonaws.com/coverage-image:v1".format(
        aws_account_id=aws_account_id
    )
