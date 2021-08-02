import os

from ..defines import GCP_CREDS_LOCAL_FILE, SupportedPython
from ..module_build_spec import ModuleBuildSpec
from ..step_builder import StepBuilder
from ..utils import connect_sibling_docker_container, network_buildkite_container
from .test_images import publish_test_images, test_image_depends_fn

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


def integration_suite_extra_cmds_fn(version):
    return [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-2 | sh",
        r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
        + GCP_CREDS_LOCAL_FILE,
        "export GOOGLE_APPLICATION_CREDENTIALS=" + GCP_CREDS_LOCAL_FILE,
        "pushd python_modules/libraries/dagster-celery",
        # Run the rabbitmq db. We are in docker running docker
        # so this will be a sibling container.
        "docker-compose up -d --remove-orphans",  # clean up in hooks/pre-exit,
        # Can't use host networking on buildkite and communicate via localhost
        # between these sibling containers, so pass along the ip.
        network_buildkite_container("rabbitmq"),
        connect_sibling_docker_container("rabbitmq", "test-rabbitmq", "DAGSTER_CELERY_BROKER_HOST"),
        "popd",
    ]


def integration_steps():
    tests = []
    tests += publish_test_images()
    tests += ModuleBuildSpec(
        os.path.join("integration_tests", "python_modules", "dagster-k8s-test-infra"),
        upload_coverage=True,
    ).get_tox_build_steps()

    integration_suites_root = os.path.join(
        SCRIPT_PATH, "..", "..", "..", "..", "integration_tests", "test_suites"
    )
    integration_suites = [
        os.path.join("integration_tests", "test_suites", suite)
        for suite in os.listdir(integration_suites_root)
    ]

    for integration_suite in integration_suites:
        tox_env_suffixes = None
        upload_coverage = False
        if integration_suite == os.path.join(
            "integration_tests", "test_suites", "k8s-integration-test-suite"
        ):
            tox_env_suffixes = ["-default"]
            upload_coverage = True
        elif integration_suite == os.path.join(
            "integration_tests", "test_suites", "celery-k8s-integration-test-suite"
        ):
            tox_env_suffixes = [
                "-default",
                "-markusercodedeployment",
                "-markusercodedeploymentsubchart",
                "-markdaemon",
            ]
            upload_coverage = True

        tests += ModuleBuildSpec(
            integration_suite,
            env_vars=[
                "AIRFLOW_HOME",
                "AWS_ACCOUNT_ID",
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "BUILDKITE_SECRETS_BUCKET",
                "GOOGLE_APPLICATION_CREDENTIALS",
            ],
            upload_coverage=upload_coverage,
            extra_cmds_fn=integration_suite_extra_cmds_fn,
            depends_on_fn=test_image_depends_fn,
            tox_env_suffixes=tox_env_suffixes,
            retries=2,
        ).get_tox_build_steps()

        tests += (
            StepBuilder("docs next")
            .run(
                "pushd docs/next",
                "yarn",
                "yarn test",
                "yarn build",
            )
            .on_integration_image(SupportedPython.V3_7)
            .build(),
        )

    return tests
