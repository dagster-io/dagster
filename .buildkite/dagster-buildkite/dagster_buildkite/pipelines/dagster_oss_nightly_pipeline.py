from typing import List

from dagster_buildkite.package_spec import PackageSpec
from dagster_buildkite.python_version import AvailablePythonVersion
from dagster_buildkite.step_builder import BuildkiteQueue
from dagster_buildkite.steps.packages import (
    build_steps_from_package_specs,
    gcp_creds_extra_cmds,
    k8s_extra_cmds,
)
from dagster_buildkite.utils import BuildkiteStep


def build_dagster_oss_nightly_steps() -> List[BuildkiteStep]:
    steps: List[BuildkiteStep] = []

    steps += build_steps_from_package_specs(
        [
            PackageSpec(
                "python_modules/libraries/dagster-dbt",
                pytest_tox_factors=["dbt18-snowflake", "dbt18-bigquery"],
                env_vars=[
                    "SNOWFLAKE_ACCOUNT",
                    "SNOWFLAKE_USER",
                    "SNOWFLAKE_PASSWORD",
                    "GCP_PROJECT_ID",
                ],
                pytest_extra_cmds=gcp_creds_extra_cmds,
                unsupported_python_versions=[
                    AvailablePythonVersion.V3_12,
                ],
                always_run_if=lambda: True,
            ),
            PackageSpec(
                "python_modules/libraries/dagster-k8s",
                env_vars=[
                    "AWS_ACCOUNT_ID",
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "BUILDKITE_SECRETS_BUCKET",
                ],
                pytest_tox_factors=[
                    "nightly",
                ],
                pytest_extra_cmds=k8s_extra_cmds,
                always_run_if=lambda: True,
            ),
            PackageSpec(
                "examples/experimental/dagster-dlift/kitchen-sink",
                name="dbt-cloud-live-tests",
                env_vars=[
                    "KS_DBT_CLOUD_ACCOUNT_ID",
                    "KS_DBT_CLOUD_PROJECT_ID",
                    "KS_DBT_CLOUD_TOKEN",
                    "KS_DBT_CLOUD_ACCESS_URL",
                    "KS_DBT_CLOUD_DISCOVERY_API_URL",
                ],
                always_run_if=lambda: True,
            ),
            PackageSpec(
                "examples/starlift-demo",
                name="airlift-demo-live-tests",
                env_vars=[
                    "KS_DBT_CLOUD_ACCOUNT_ID",
                    "KS_DBT_CLOUD_PROJECT_ID",
                    "KS_DBT_CLOUD_TOKEN",
                    "KS_DBT_CLOUD_ACCESS_URL",
                    "KS_DBT_CLOUD_DISCOVERY_API_URL",
                ],
                queue=BuildkiteQueue.DOCKER,
                always_run_if=lambda: True,
            ),
            PackageSpec(
                "integration_tests/test_suites/dagster-azure-live-tests",
                name="azure-live-tests",
                env_vars=[
                    "TEST_AZURE_TENANT_ID",
                    "TEST_AZURE_CLIENT_ID",
                    "TEST_AZURE_CLIENT_SECRET",
                    "TEST_AZURE_STORAGE_ACCOUNT_ID",
                    "TEST_AZURE_CONTAINER_ID",
                    "TEST_AZURE_ACCESS_KEY",
                ],
                always_run_if=lambda: True,
            ),
            PackageSpec(
                "integration_tests/test_suites/dagster-gcp-live-tests",
                name="gcp-live-tests",
                env_vars=["GCP_LIVE_TEST_CREDENTIALS"],
                always_run_if=lambda: True,
            ),
        ]
    )

    return steps
