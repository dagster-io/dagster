import os
from typing import List, Optional, Set

from dagster_buildkite.defines import GCP_CREDS_FILENAME, GCP_CREDS_LOCAL_FILE
from dagster_buildkite.images.versions import (
    BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION,
    TEST_PROJECT_BASE_IMAGE_VERSION,
)
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import CommandStepBuilder
from dagster_buildkite.utils import BuildkiteLeafStep, GroupStep

# Some python packages depend on these images but we don't explicitly define that dependency anywhere other
# than when we construct said package's Buildkite steps. Until we more explicitly define those dependencies
# somewhere, we use these sets to track internal state about whether or not to build the test-project images
#
# When we build the Buildkite steps for a python package that needs one or both of these images, add the
# required versions to these sets. We'll otherwise skip building images for any versions not requested here.
#
# This means you need to call `build_test_project_steps()` after you've build the other Buildkite steps that
# require the images.
#
# TODO: Don't do this :) More explicitly define the dependencies.
# See https://github.com/dagster-io/dagster/pull/10099 for implementation ideas.
build_test_project_for: Set[AvailablePythonVersion] = set()


def build_test_project_steps() -> List[GroupStep]:
    """This set of tasks builds and pushes Docker images, which are used by the dagster-airflow and
    the dagster-k8s tests.
    """
    steps: List[BuildkiteLeafStep] = []

    # Build for all available versions because a dependent extension might need to run tests on any version.
    py_versions = AvailablePythonVersion.get_all()

    for version in py_versions:
        key = _test_project_step_key(version)
        steps.append(
            CommandStepBuilder(f":docker: test-project {version}", key=key)
            # these run commands are coupled to the way the buildkite-build-test-project-image is built
            # see python_modules/automation/automation/docker/images/buildkite-build-test-project-image
            .run(
                # credentials
                "/scriptdir/aws.pex ecr get-login --no-include-email --region us-west-2 | sh",
                f'export GOOGLE_APPLICATION_CREDENTIALS="{GCP_CREDS_LOCAL_FILE}"',
                "/scriptdir/aws.pex s3 cp"
                f" s3://$${{BUILDKITE_SECRETS_BUCKET}}/{GCP_CREDS_FILENAME}"
                " $${GOOGLE_APPLICATION_CREDENTIALS}",
                "export"
                " BASE_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/test-project-base:py"
                + version
                + "-"
                + TEST_PROJECT_BASE_IMAGE_VERSION,
                # build and tag test image
                "export"
                " TEST_PROJECT_IMAGE=$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/test-project:$${BUILDKITE_BUILD_ID}-"
                + version,
                "git config --global --add safe.directory /workdir",
                "./python_modules/dagster-test/dagster_test/test_project/build.sh "
                + version
                + " $${TEST_PROJECT_IMAGE}",
                #
                # push the built image
                'echo -e "--- \033[32m:docker: Pushing Docker image\033[0m"',
                "docker push $${TEST_PROJECT_IMAGE}",
            )
            .on_python_image(
                # py version can be bumped when rebuilt
                f"buildkite-build-test-project-image:py{AvailablePythonVersion.V3_8}-{BUILDKITE_BUILD_TEST_PROJECT_IMAGE_IMAGE_VERSION}",
                [
                    "AIRFLOW_HOME",
                    "AWS_ACCOUNT_ID",
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "BUILDKITE_SECRETS_BUCKET",
                ],
            )
            .with_skip(skip_if_version_not_needed(version))
            .build()
        )

    return [
        GroupStep(
            group=":docker: test-project-image",
            key="test-project-image",
            steps=steps,
        )
    ]


def _test_project_step_key(version: AvailablePythonVersion) -> str:
    return f"sample-project-{AvailablePythonVersion.to_tox_factor(version)}"


def test_project_depends_fn(version: AvailablePythonVersion, _) -> List[str]:
    if not os.getenv("CI_DISABLE_INTEGRATION_TESTS"):
        build_test_project_for.add(version)
        return [_test_project_step_key(version)]
    else:
        return []


def skip_if_version_not_needed(version: AvailablePythonVersion) -> Optional[str]:
    if version in build_test_project_for:
        return None

    return "Skipped because no build depends on this image"
