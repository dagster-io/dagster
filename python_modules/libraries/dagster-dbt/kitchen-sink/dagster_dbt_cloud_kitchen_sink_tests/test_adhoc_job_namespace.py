import os
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, cast
from unittest import mock

import pytest
from dagster_dbt.cloud_v2.resources import DAGSTER_ADHOC_PREFIX
from dagster_dbt_cloud_kitchen_sink.cleanup import (
    destroy_adhoc_jobs_in_namespace,
    sweep_orphaned_adhoc_jobs,
)
from dagster_dbt_cloud_kitchen_sink.resources import (
    CI_ADHOC_JOB_PREFIX,
    build_adhoc_job_namespace,
    get_adhoc_job_namespace,
    get_build_token,
    parse_adhoc_job_created_at,
)

if TYPE_CHECKING:
    from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient

PROJECT_ID = 1
ENVIRONMENT_ID = 2


class FakeClient:
    """Stands in for DbtCloudWorkspaceClient, recording which jobs were destroyed.

    ``failing_job_ids`` raise on delete, standing in for a job another run reclaimed first.
    """

    def __init__(
        self, jobs: Sequence[Mapping[str, Any]], failing_job_ids: Sequence[int] = ()
    ) -> None:
        self.jobs = list(jobs)
        self.failing_job_ids = set(failing_job_ids)
        self.destroyed_job_ids: list[int] = []

    def list_jobs(self, project_id: int, environment_id: int) -> Sequence[Mapping[str, Any]]:
        assert (project_id, environment_id) == (PROJECT_ID, ENVIRONMENT_ID)
        return self.jobs

    def destroy_job(self, job_id: int) -> None:
        if job_id in self.failing_job_ids:
            raise Exception(f"Not found: {job_id}")
        self.destroyed_job_ids.append(job_id)


def _destroy(client: FakeClient, namespace: str) -> Sequence[int]:
    return destroy_adhoc_jobs_in_namespace(
        client=cast("DbtCloudWorkspaceClient", client),
        project_id=PROJECT_ID,
        environment_id=ENVIRONMENT_ID,
        namespace=namespace,
    )


def _sweep(client: FakeClient, now: float, max_age_seconds: int = 100) -> Sequence[int]:
    return sweep_orphaned_adhoc_jobs(
        client=cast("DbtCloudWorkspaceClient", client),
        project_id=PROJECT_ID,
        environment_id=ENVIRONMENT_ID,
        max_age_seconds=max_age_seconds,
        now=now,
    )


# ##### TESTS


def test_build_token_identifies_the_build() -> None:
    with mock.patch.dict(os.environ, {"BUILDKITE_BUILD_ID": "0198-abc-DEF"}):
        assert get_build_token() == "0198_ABC_DEF"
        # Two builds of the same commit must not collapse onto the same token.
        with mock.patch.dict(os.environ, {"BUILDKITE_BUILD_ID": "0198-abc-DEF0"}):
            assert get_build_token() != "0198_ABC_DEF"

    with mock.patch.dict(os.environ):
        os.environ.pop("BUILDKITE_BUILD_ID", None)
        local_token = get_build_token()
    # "__" separates namespace segments, so a token must never contain one.
    assert local_token and "__" not in local_token


def test_namespace_round_trips_and_is_stable_within_a_run() -> None:
    namespace = build_adhoc_job_namespace(created_at=1700000000, build_token="BUILD")
    assert namespace == f"{CI_ADHOC_JOB_PREFIX}1700000000__BUILD"
    assert parse_adhoc_job_created_at(namespace) == 1700000000
    # A run's teardown must reclaim what its setup created, so the value is cached.
    assert get_adhoc_job_namespace() == get_adhoc_job_namespace()
    assert get_adhoc_job_namespace().startswith(CI_ADHOC_JOB_PREFIX)


@pytest.mark.parametrize(
    "job_name,expected",
    [
        (f"{CI_ADHOC_JOB_PREFIX}1700000000__BUILD", 1700000000),
        # Pool entries carry an index suffix.
        (f"{CI_ADHOC_JOB_PREFIX}1700000000__BUILD__1", 1700000000),
        # Jobs belonging to a real deployment, or to the pre-namespacing scheme.
        (f"{DAGSTER_ADHOC_PREFIX}123__456", None),
        ("MY_NIGHTLY_JOB", None),
        # Malformed namespaces are left alone rather than guessed at.
        (f"{CI_ADHOC_JOB_PREFIX}NOT_A_TIMESTAMP__BUILD", None),
        (CI_ADHOC_JOB_PREFIX, None),
    ],
)
def test_parse_adhoc_job_created_at(job_name: str, expected: int | None) -> None:
    assert parse_adhoc_job_created_at(job_name) == expected


def test_destroy_only_touches_this_builds_jobs() -> None:
    namespace = f"{CI_ADHOC_JOB_PREFIX}1700000000__MINE"
    client = FakeClient(
        [
            {"id": 1, "name": namespace},
            {"id": 2, "name": f"{namespace}__1"},
            {"id": 3, "name": f"{namespace}__CLIENT_TEST"},
            {"id": 4, "name": f"{CI_ADHOC_JOB_PREFIX}1700000000__THEIRS"},
            {"id": 5, "name": f"{DAGSTER_ADHOC_PREFIX}123__456"},
            {"id": 6, "name": "CUSTOMER_NIGHTLY"},
            {"id": 7, "name": None},
        ]
    )

    assert _destroy(client, namespace) == [1, 2, 3]
    assert client.destroyed_job_ids == [1, 2, 3]


def test_sweep_only_reclaims_aged_ci_jobs() -> None:
    client = FakeClient(
        [
            {"id": 1, "name": f"{CI_ADHOC_JOB_PREFIX}1000__OLD"},
            {"id": 2, "name": f"{CI_ADHOC_JOB_PREFIX}1000__OLD__1"},
            # In flight right now — another build is using this.
            {"id": 3, "name": f"{CI_ADHOC_JOB_PREFIX}1950__RUNNING"},
            # Exactly at the cutoff counts as still live.
            {"id": 4, "name": f"{CI_ADHOC_JOB_PREFIX}1900__BORDERLINE"},
            # Never swept by age: not ours to reclaim.
            {"id": 5, "name": f"{DAGSTER_ADHOC_PREFIX}123__456"},
            {"id": 6, "name": "CUSTOMER_NIGHTLY"},
        ]
    )

    assert _sweep(client, now=2000) == [1, 2]
    assert client.destroyed_job_ids == [1, 2]


def test_a_lost_delete_race_does_not_strand_the_remaining_jobs() -> None:
    namespace = f"{CI_ADHOC_JOB_PREFIX}1700000000__MINE"
    client = FakeClient(
        [
            {"id": 1, "name": namespace},
            {"id": 2, "name": f"{namespace}__1"},
            {"id": 3, "name": f"{namespace}__2"},
        ],
        failing_job_ids=[2],
    )

    # Job 2 is already gone, which is the outcome we wanted; 3 must still be reclaimed.
    assert _destroy(client, namespace) == [1, 3]
    assert client.destroyed_job_ids == [1, 3]
