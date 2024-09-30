from typing import List

from dagster_buildkite.package_spec import PackageSpec
from dagster_buildkite.python_version import AvailablePythonVersion
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
            ),
        ]
    )

    return steps
