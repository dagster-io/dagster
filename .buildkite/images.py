from defines import TOX_MAP, UNIT_IMAGE_VERSION, SupportedPythons
from step_builder import StepBuilder


def publish_test_images():
    """This set of tasks builds and pushes Docker images, which are used by the dagster-airflow and
    the dagster-k8s tests
    """
    tests = []
    for version in SupportedPythons:
        key = "dagster-test-images-{version}".format(version=TOX_MAP[version])
        tests.append(
            StepBuilder("test images {version}".format(version=version), key=key)
            # these run commands are coupled to the way the test-image-builder is built
            # see .buildkite/images/test_image_builder/Dockerfile
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-1 | sh",
                'export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-key-elementl-dev.json"',
                "/scriptdir/aws.pex s3 cp s3://$${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $${GOOGLE_APPLICATION_CREDENTIALS}",
                #
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-docker-buildkite:$${BUILDKITE_BUILD_ID}-"
                + version,
                "./python_modules/dagster-test/dagster_test/test_project/build.sh "
                + version
                + " $${TEST_IMAGE}",
                #
                # push the built image
                'echo -e "--- \033[32m:docker: Pushing Docker image\033[0m"',
                "docker push $${TEST_IMAGE}",
            )
            .on_python_image(
                "test-image-builder:v2",
                [
                    "AIRFLOW_HOME",
                    "AWS_ACCOUNT_ID",
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "BUILDKITE_SECRETS_BUCKET",
                ],
            )
            .build()
        )

        key = "dagster-core-test-images-{version}".format(version=TOX_MAP[version])
        tests.append(
            StepBuilder("core test images {version}".format(version=version), key=key)
            # these run commands are coupled to the way the test-image-builder is built
            # see .buildkite/images/test_image_builder/Dockerfile
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-1 | sh",
                # set the base image
                "export BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-unit:py"
                + version
                + "-"
                + UNIT_IMAGE_VERSION,
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-core-docker-buildkite:$${BUILDKITE_BUILD_ID}-"
                + version,
                "./python_modules/dagster-test/build_core.sh " + version + " $${TEST_IMAGE}",
                #
                # push the built image
                'echo -e "--- \033[32m:docker: Pushing Docker image\033[0m"',
                "docker push $${TEST_IMAGE}",
            )
            .on_python_image(
                "test-image-builder:v2",
                [
                    "AWS_ACCOUNT_ID",
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "BUILDKITE_SECRETS_BUCKET",
                ],
            )
            .build()
        )
    return tests


def test_image_depends_fn(version):
    return ["dagster-test-images-{version}".format(version=TOX_MAP[version])]
