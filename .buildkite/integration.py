import os

import yaml
from defines import SupportedPython3s
from module_build_spec import ModuleBuildSpec
from pipeline import GCP_CREDS_LOCAL_FILE, publish_test_images, test_image_depends_fn
from utils import connect_sibling_docker_container, network_buildkite_container

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


def integration_suite_extra_cmds_fn(version):
    return [
        'export AIRFLOW_HOME="/airflow"',
        "mkdir -p $${AIRFLOW_HOME}",
        "export DAGSTER_DOCKER_IMAGE_TAG=$${BUILDKITE_BUILD_ID}-" + version,
        'export DAGSTER_DOCKER_REPOSITORY="$${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com"',
        "aws ecr get-login --no-include-email --region us-west-1 | sh",
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


def integration_tests():
    tests = []
    tests += publish_test_images()
    tests += ModuleBuildSpec(
        os.path.join("integration_tests", "python_modules", "dagster-k8s-test-infra"),
        supported_pythons=SupportedPython3s,
        upload_coverage=True,
    ).get_tox_build_steps()

    integration_suites_root = os.path.join(SCRIPT_PATH, "..", "integration_tests", "test_suites")
    integration_suites = [
        os.path.join("integration_tests", "test_suites", suite)
        for suite in os.listdir(integration_suites_root)
    ]

    for integration_suite in integration_suites:
        tox_env_suffixes = None
        if integration_suite == os.path.join(
            "integration_tests", "test_suites", "k8s-integration-test-suite"
        ):
            tox_env_suffixes = ["-default", "-markscheduler"]
        elif integration_suite == os.path.join(
            "integration_tests", "test_suites", "celery-k8s-integration-test-suite"
        ):
            tox_env_suffixes = ["-default", "-markusercodedeployment"]

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
            supported_pythons=SupportedPython3s,
            upload_coverage=True,
            extra_cmds_fn=integration_suite_extra_cmds_fn,
            depends_on_fn=test_image_depends_fn,
            tox_env_suffixes=tox_env_suffixes,
            retries=2,
        ).get_tox_build_steps()
    return tests


if __name__ == "__main__":
    print(  # pylint: disable=print-call
        yaml.dump(
            {
                "env": {
                    "CI_NAME": "buildkite",
                    "CI_BUILD_NUMBER": "$BUILDKITE_BUILD_NUMBER",
                    "CI_BUILD_URL": "$BUILDKITE_BUILD_URL",
                    "CI_BRANCH": "$BUILDKITE_BRANCH",
                    "CI_PULL_REQUEST": "$BUILDKITE_PULL_REQUEST",
                },
                "steps": integration_tests(),
            },
            default_flow_style=False,
        )
    )
