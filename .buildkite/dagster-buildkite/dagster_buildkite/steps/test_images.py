from typing import List

from ..images.versions import (
    BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION,
    TEST_PROJECT_BASE_IMAGE_VERSION,
)
from ..python_version import AvailablePythonVersion
from ..step_builder import CommandStepBuilder
from ..utils import BuildkiteLeafStep, GroupStep


def build_test_image_steps() -> List[GroupStep]:
    """This set of tasks builds and pushes Docker images, which are used by the dagster-airflow and
    the dagster-k8s tests
    """
    steps: List[BuildkiteLeafStep] = []

    # Build for all available versions because a dependent extension might need to run tests on any
    # version.
    py_versions = AvailablePythonVersion.get_all()

    for version in py_versions:
        key = _test_image_step(version)
        steps.append(
            CommandStepBuilder(f":docker: test-image {version}", key=key)
            # these run commands are coupled to the way the buildkite-build-test-project-image is built
            # see python_modules/automation/automation/docker/images/buildkite-build-test-project-image
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-2 | sh",
                'export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-key-elementl-dev.json"',
                "/scriptdir/aws.pex s3 cp s3://$${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $${GOOGLE_APPLICATION_CREDENTIALS}",
                "export BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/test-project-base:py"
                + version
                + "-"
                + TEST_PROJECT_BASE_IMAGE_VERSION,
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/test-project:$${BUILDKITE_BUILD_ID}-"
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
                "buildkite-build-test-project-image:py{python_version}-{image_version}".format(
                    python_version=AvailablePythonVersion.V3_8,
                    image_version=BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION,
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
        steps.append(
            CommandStepBuilder(f":docker: test-image-core {version}", key=key)
            # these run commands are coupled to the way the buildkite-build-test-project-image is built
            # see python_modules/automation/automation/docker/images/buildkite-build-test-project-image
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-2 | sh",
                # set the base image
                "export BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/test-project-base:py"
                + version
                + "-"
                + TEST_PROJECT_BASE_IMAGE_VERSION,
                # build and tag test image
                "export TEST_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/test-project-core:$${BUILDKITE_BUILD_ID}-"
                + version,
                "./python_modules/dagster-test/build_core.sh " + version + " $${TEST_IMAGE}",
                #
                # push the built image
                'echo -e "--- \033[32m:docker: Pushing Docker image\033[0m"',
                "docker push $${TEST_IMAGE}",
            )
            .on_python_image(
                "buildkite-build-test-project-image:py{python_version}-{image_version}".format(
                    python_version=AvailablePythonVersion.V3_8,
                    image_version=BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION,
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
    return [
        GroupStep(
            group=":docker: test-image",
            key="test-image",
            steps=steps,
        )
    ]


def _test_image_step(version: AvailablePythonVersion) -> str:
    return f"dagster-test-images-{AvailablePythonVersion.to_tox_factor(version)}"


def test_image_depends_fn(version: AvailablePythonVersion, _) -> List[str]:
    return [_test_image_step(version)]


def _core_test_image_step(version: AvailablePythonVersion) -> str:
    return f"dagster-core-test-images-{AvailablePythonVersion.to_tox_factor(version)}"


def core_test_image_depends_fn(version: AvailablePythonVersion, _) -> List[str]:
    return [_core_test_image_step(version)]
