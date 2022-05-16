from typing import List
from ..defines import TOX_MAP, SupportedPython
from ..images.versions import TEST_IMAGE_BUILDER_VERSION, UNIT_IMAGE_VERSION
from ..step_builder import StepBuilder
from ..utils import get_python_versions_for_branch


def publish_test_images():
    """This set of tasks builds and pushes Docker images, which are used by the dagster-airflow and
    the dagster-k8s tests
    """
    tests = []
    for version in get_python_versions_for_branch(
        pr_versions=[SupportedPython.V3_8, SupportedPython.V3_9]
    ):
        key = _test_image_step(version)
        tests.append(
            StepBuilder(f":docker: test-image {version}", key=key)
            # these run commands are coupled to the way the test-image-builder is built
            # see python_modules/automation/automation/docker/images/buildkite-test-image-builder
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-2 | sh",
                'export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-key-elementl-dev.json"',
                "/scriptdir/aws.pex s3 cp s3://$${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $${GOOGLE_APPLICATION_CREDENTIALS}",
                "export BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/buildkite-unit:py"
                + version
                + "-"
                + UNIT_IMAGE_VERSION,
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/buildkite-test-image:$${BUILDKITE_BUILD_ID}-"
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
                "buildkite-test-image-builder:py{python_version}-{image_version}".format(
                    python_version=SupportedPython.V3_8, image_version=TEST_IMAGE_BUILDER_VERSION
                ),
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

        key = _core_test_image_step(version)
        tests.append(
            StepBuilder(f":docker: test-image-core {version}", key=key)
            # these run commands are coupled to the way the test-image-builder is built
            # see python_modules/automation/automation/docker/images/buildkite-test-image-builder
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-2 | sh",
                # set the base image
                "export BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/buildkite-unit:py"
                + version
                + "-"
                + UNIT_IMAGE_VERSION,
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/buildkite-test-image-core:$${BUILDKITE_BUILD_ID}-"
                + version,
                "./python_modules/dagster-test/build_core.sh " + version + " $${TEST_IMAGE}",
                #
                # push the built image
                'echo -e "--- \033[32m:docker: Pushing Docker image\033[0m"',
                "docker push $${TEST_IMAGE}",
            )
            .on_python_image(
                "buildkite-test-image-builder:py{python_version}-{image_version}".format(
                    python_version=SupportedPython.V3_8, image_version=TEST_IMAGE_BUILDER_VERSION
                ),
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


def _test_image_step(version: str) -> str:
    return f"dagster-test-images-{TOX_MAP[version]}"


def test_image_depends_fn(version: str) -> List[str]:
    return [_test_image_step(version)]


def _core_test_image_step(version: str) -> str:
    return f"dagster-core-test-images-{TOX_MAP[version]}"


def core_test_image_depends_fn(version: str) -> List[str]:
    return [_core_test_image_step(version)]
