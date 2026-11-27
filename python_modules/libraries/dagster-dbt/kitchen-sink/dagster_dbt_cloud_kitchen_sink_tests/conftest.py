import logging
from collections.abc import Generator, Sequence

import dagster as dg
import pytest
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace, load_dbt_cloud_asset_specs
from dagster_dbt_cloud_kitchen_sink.cleanup import (
    destroy_adhoc_jobs_in_namespace,
    sweep_orphaned_adhoc_jobs,
)
from dagster_dbt_cloud_kitchen_sink.resources import (
    get_adhoc_job_namespace,
    get_dbt_cloud_workspace,
    get_environment_id,
    get_project_id,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def ensure_cleanup() -> Generator[None, None, None]:
    """Reclaims the dbt Cloud ad hoc jobs this run is responsible for.

    On the way in, sweeps jobs leaked by builds that died before their teardown ran.
    On the way out, deletes the jobs this run created — and only those, so a concurrent
    build's jobs survive.

    Both halves are best-effort: neither a sweep nor a teardown failure should fail the
    suite, and a developer without dbt Cloud credentials can still run the offline tests.
    """
    client = None
    namespace = get_adhoc_job_namespace()
    try:
        client = get_dbt_cloud_workspace().get_client()
        swept_job_ids = sweep_orphaned_adhoc_jobs(
            client=client,
            project_id=get_project_id(),
            environment_id=get_environment_id(),
        )
        logger.info(f"Swept orphaned ad hoc dbt Cloud jobs: {swept_job_ids}.")
    except Exception:
        logger.exception("Failed to sweep orphaned ad hoc dbt Cloud jobs.")

    try:
        yield
    finally:
        if client is not None:
            try:
                destroyed_job_ids = destroy_adhoc_jobs_in_namespace(
                    client=client,
                    project_id=get_project_id(),
                    environment_id=get_environment_id(),
                    namespace=namespace,
                )
                logger.info(f"Destroyed ad hoc dbt Cloud jobs: {destroyed_job_ids}.")
            except Exception:
                logger.exception("Failed to destroy this run's ad hoc dbt Cloud jobs.")


@pytest.fixture
def workspace() -> DbtCloudWorkspace:
    return get_dbt_cloud_workspace()


@pytest.fixture
def project_id() -> int:
    return get_project_id()


@pytest.fixture
def environment_id() -> int:
    return get_environment_id()


@pytest.fixture
def adhoc_job_namespace() -> str:
    return get_adhoc_job_namespace()


@pytest.fixture
def dbt_cloud_specs() -> Sequence[dg.AssetSpec]:
    """Asset specs fetched from the live dbt Cloud workspace.

    Fetched in a fixture rather than at import time so a slow or queued dbt Cloud run
    surfaces as a rerunnable test failure instead of aborting pytest collection.
    Function-scoped because pytest caches a broader-scoped fixture's error, which would
    make every rerun fail identically without retrying the fetch.
    """
    return load_dbt_cloud_asset_specs(workspace=get_dbt_cloud_workspace())
