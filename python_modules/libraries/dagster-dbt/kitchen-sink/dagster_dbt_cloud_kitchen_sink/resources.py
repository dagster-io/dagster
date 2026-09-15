import getpass
import os
import re
import time
from functools import cache

from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace

from dagster_dbt_cloud_kitchen_sink.utils import get_env_var

# Ad hoc jobs created by this suite are namespaced under this prefix so cleanup can
# target them without touching jobs owned by another build or by a real deployment.
# The prefix itself contains no "__" so the segments after it parse unambiguously.
CI_ADHOC_JOB_PREFIX = "DAGSTER_ADHOC_CI__"


def get_project_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_PROJECT_ID"))


def get_environment_id() -> int:
    return int(get_env_var("KS_DBT_CLOUD_ENVIRONMENT_ID"))


def _sanitize(value: str) -> str:
    """Collapse runs of non-alphanumerics to a single underscore, so the result never
    contains the "__" that separates namespace segments.
    """
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()


def get_build_token() -> str:
    """Identifier for the process running this suite, unique across concurrent CI builds."""
    build_id = os.getenv("BUILDKITE_BUILD_ID")
    if build_id:
        return _sanitize(build_id)
    return _sanitize(f"{getpass.getuser()}_{os.getpid()}")


def build_adhoc_job_namespace(created_at: int, build_token: str) -> str:
    """Ad hoc dbt Cloud job name scoped to one test run.

    The dbt Cloud account is shared across concurrent CI builds and dbt Cloud allows
    only one concurrent run per job, so every build needs its own job rather than the
    deterministic name ``DbtCloudWorkspace`` derives from project/environment IDs.

    The creation time is embedded in the name so a later build can sweep jobs leaked
    by a build that died before its teardown ran.
    """
    return f"{CI_ADHOC_JOB_PREFIX}{created_at}__{build_token}"


@cache
def get_adhoc_job_namespace() -> str:
    """The ad hoc job namespace for this run. Cached so teardown reclaims what setup created."""
    return build_adhoc_job_namespace(created_at=int(time.time()), build_token=get_build_token())


def parse_adhoc_job_created_at(job_name: str) -> int | None:
    """Epoch seconds encoded in a CI-namespaced ad hoc job name, or None if it isn't one."""
    if not job_name.startswith(CI_ADHOC_JOB_PREFIX):
        return None
    created_at, _, _ = job_name[len(CI_ADHOC_JOB_PREFIX) :].partition("__")
    return int(created_at) if created_at.isdigit() else None


def get_dbt_cloud_workspace() -> DbtCloudWorkspace:
    return DbtCloudWorkspace(
        credentials=DbtCloudCredentials(
            account_id=int(get_env_var("KS_DBT_CLOUD_ACCOUNT_ID")),
            access_url=get_env_var("KS_DBT_CLOUD_ACCESS_URL"),
            token=get_env_var("KS_DBT_CLOUD_TOKEN"),
        ),
        project_id=get_project_id(),
        environment_id=get_environment_id(),
        adhoc_job_name=get_adhoc_job_namespace(),
    )
