import sys
from contextlib import contextmanager

import dagster as dg
import dagster._check as check
import pytest
from dagster import job
from dagster._api.snapshot_repository import sync_get_external_repositories_data_grpc
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_origin import (
    ManagedGrpcPythonEnvCodeLocationOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import (
    DISABLE_FAST_EXTRACT_ENV_VAR,
    JobDataSnap,
    JobRefSnap,
    RepositorySnap,
    extract_serialized_job_snap_from_serialized_job_data_snap,
)
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.tags import EXTERNAL_JOB_SOURCE_TAG_KEY
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._utils.env import environ
from dagster_shared.serdes.serdes import get_storage_fields
from dagster_shared.serdes.utils import hash_str

from dagster_tests.api_tests.utils import get_bar_repo_code_location


def test_external_repositories_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_snaps = sync_get_external_repositories_data_grpc(
            code_location.client, code_location, defer_snapshots=False
        )

        assert len(repository_snaps) == 1

        repository_snap, job_data_snaps = repository_snaps["bar_repo"]

        assert isinstance(repository_snap, RepositorySnap)
        assert repository_snap.name == "bar_repo"
        assert repository_snap.metadata == {
            "string": dg.TextMetadataValue("foo"),
            "integer": dg.IntMetadataValue(123),
        }

        assert len(check.not_none(repository_snap.job_datas)) == 8
        assert not repository_snap.job_refs

        assert not job_data_snaps


def test_external_repositories_api_grpc_defer_snapshots(instance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_snaps = sync_get_external_repositories_data_grpc(
            code_location.client, code_location, defer_snapshots=True
        )

        assert len(repository_snaps) == 1

        repository_snap, job_data_snaps = repository_snaps["bar_repo"]

        assert isinstance(repository_snap, RepositorySnap)
        assert repository_snap.name == "bar_repo"
        assert repository_snap.metadata == {
            "string": dg.TextMetadataValue("foo"),
            "integer": dg.IntMetadataValue(123),
        }

        assert not repository_snap.job_datas
        assert len(check.not_none(repository_snap.job_refs)) == 8

        assert len(check.not_none(job_data_snaps)) == 8


def test_streaming_external_repositories_error(instance):
    with get_bar_repo_code_location(instance) as code_location:
        code_location.repository_names = {"does_not_exist"}
        assert code_location.repository_names == {"does_not_exist"}

        with pytest.raises(
            DagsterUserCodeProcessError,
            match='Could not find a repository called "does_not_exist"',
        ):
            sync_get_external_repositories_data_grpc(
                code_location.client, code_location, defer_snapshots=True
            )


@dg.op
def do_something():
    return 1


@job
def giant_job():
    # Job big enough to be larger than the max size limit for a gRPC message in its
    # external repository
    for _i in range(20000):
        do_something()


@dg.repository
def giant_repo():
    return {
        "jobs": {
            "giant": giant_job,
        },
    }


@contextmanager
def get_giant_repo_grpc_code_location(instance):
    with ManagedGrpcPythonEnvCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="giant_repo",
            module_name="dagster_tests.api_tests.test_api_snapshot_repository",
        ),
        location_name="giant_repo_location",
    ).create_single_location(instance) as location:
        yield location


@pytest.mark.skip("https://github.com/dagster-io/dagster/issues/6940")
def test_giant_external_repository_streaming_grpc():
    with dg.instance_for_test() as instance:
        with get_giant_repo_grpc_code_location(instance) as code_location:
            # Using streaming allows the giant repo to load
            repository_snaps = sync_get_external_repositories_data_grpc(
                code_location.client, code_location, defer_snapshots=True
            )

            assert len(repository_snaps) == 1

            repository_snap = repository_snaps["giant_repo"]

            assert isinstance(repository_snap, RepositorySnap)
            assert repository_snap.name == "giant_repo"


@pytest.mark.parametrize("env", [{}, {DISABLE_FAST_EXTRACT_ENV_VAR: "true"}])
def test_defer_snapshots(instance: DagsterInstance, env):
    with get_bar_repo_code_location(instance) as code_location, environ(env):
        repo_origin = RemoteRepositoryOrigin(
            code_location.origin,
            "bar_repo",
        )

        ser_repo_data = code_location.client.external_repository(
            repo_origin,
            defer_snapshots=True,
        )

        _state = {}

        def _ref_to_data(ref: JobRefSnap):
            _state["cnt"] = _state.get("cnt", 0) + 1
            reply = code_location.client.external_job(
                repo_origin,
                ref.name,
            )
            assert reply.serialized_job_data, reply.serialized_error
            assert (
                hash_str(
                    extract_serialized_job_snap_from_serialized_job_data_snap(
                        reply.serialized_job_data
                    )
                )
                == ref.snapshot_id
            ), ref.name

            job_data_snap = dg.deserialize_value(reply.serialized_job_data, JobDataSnap)
            return job_data_snap

        repository_snap = dg.deserialize_value(ser_repo_data, RepositorySnap)
        assert repository_snap.job_refs and len(repository_snap.job_refs) == 8
        assert repository_snap.job_datas is None

        repo = RemoteRepository(
            repository_snap,
            RepositoryHandle.from_location(repository_name="bar_repo", code_location=code_location),
            auto_materialize_use_sensors=True,
            ref_to_data_fn=_ref_to_data,
        )
        jobs = repo.get_all_jobs()
        assert len(jobs) == 8
        assert _state.get("cnt", 0) == 0

        job = jobs[0]

        # basic accessors should not cause a fetch
        _ = job.computed_job_snapshot_id
        assert _state.get("cnt", 0) == 0

        _ = job.name
        assert _state.get("cnt", 0) == 0

        _ = job.active_presets
        assert _state.get("cnt", 0) == 0

        _ = job.job_snapshot
        assert _state.get("cnt", 0) == 1

        # access should be memoized
        _ = job.job_snapshot
        assert _state.get("cnt", 0) == 1

        # refetching job should share fetched data
        expected = 1  # from job[0] access
        for job in repo.get_all_jobs():
            _ = job.job_snapshot
            assert _state.get("cnt", 0) == expected
            expected += 1

        # Test that the external job source is available on the relevant job ref snap.
        external_job_ref = next(
            ref for ref in repository_snap.job_refs if ref.name == "job_with_external_tag"
        )
        assert external_job_ref.get_preview_tags().get(EXTERNAL_JOB_SOURCE_TAG_KEY) == "airflow"
        assert "foo" not in external_job_ref.get_preview_tags()


def test_job_data_snap_layout():
    # defend against assumptions made in

    # must remain last position
    assert get_storage_fields(JobDataSnap)[-1] == "pipeline_snapshot"


@pytest.mark.parametrize("streaming", [False, True])
def test_external_repository_compact_serdes(instance, streaming):
    import asyncio

    from dagster_shared.serdes.compact import is_compact_serialized

    with get_bar_repo_code_location(instance) as code_location:
        repo_origin = RemoteRepositoryOrigin(code_location.origin, "bar_repo")

        async def _fetch(compact_serdes: bool) -> str:
            if streaming:
                chunks = [
                    chunk["serialized_external_repository_chunk"]
                    async for chunk in code_location.client.gen_streaming_external_repository(
                        repo_origin, defer_snapshots=True, compact_serdes=compact_serdes
                    )
                ]
                return "".join(chunks)
            return await code_location.client.gen_external_repository(
                repo_origin, defer_snapshots=True, compact_serdes=compact_serdes
            )

        legacy = asyncio.run(_fetch(compact_serdes=False))
        compact = asyncio.run(_fetch(compact_serdes=True))
        assert not is_compact_serialized(legacy)
        assert is_compact_serialized(compact)
        assert dg.deserialize_value(compact, RepositorySnap) == dg.deserialize_value(
            legacy, RepositorySnap
        )


@pytest.mark.parametrize(
    "env_value,expect_compact",
    [(None, True), ("", True), ("0", True), ("false", True), ("1", False), ("true", False)],
)
def test_client_requests_compact_snapshots(instance, env_value, expect_compact):
    from dagster._api.snapshot_repository import DISABLE_COMPACT_SNAPSHOTS_ENV_VAR

    with get_bar_repo_code_location(instance) as code_location:
        requested = []
        original = code_location.client.external_repository

        def _external_repository(*args, **kwargs):
            requested.append(kwargs["compact_serdes"])
            return original(*args, **kwargs)

        code_location.client.external_repository = _external_repository  # type: ignore
        with environ({DISABLE_COMPACT_SNAPSHOTS_ENV_VAR: env_value}):
            repo_datas = sync_get_external_repositories_data_grpc(
                code_location.client, code_location, defer_snapshots=True
            )
        assert requested == [expect_compact]
        assert repo_datas["bar_repo"][0].name == "bar_repo"


def test_server_falls_back_to_legacy_format(monkeypatch):
    import logging
    import threading

    from dagster._grpc import server as server_module
    from dagster._grpc.__generated__ import dagster_api_pb2
    from dagster_shared.serdes.compact import is_compact_serialized

    def _broken(*args, **kwargs):
        raise Exception("broken compact encoder")

    monkeypatch.setattr(server_module, "serialize_value_compact", _broken)
    with get_bar_repo_code_location() as code_location:
        repo_origin = RemoteRepositoryOrigin(code_location.origin, "bar_repo")
        # serve the same definitions from this process, so that the patch applies
        servicer = server_module.DagsterApiServer(
            server_termination_event=threading.Event(),
            logger=logging.getLogger("test"),
            server_threadpool_executor=None,  # type: ignore
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=dg.file_relative_path(__file__, "api_tests_repo.py"),
                attribute="bar_repo",
            ),
        )
        serialized = servicer._get_serialized_external_repository_data(  # noqa: SLF001
            dagster_api_pb2.ExternalRepositoryRequest(
                serialized_repository_python_origin=dg.serialize_value(repo_origin),
                defer_snapshots=True,
                compact_serdes=True,
            )
        )
    assert not is_compact_serialized(serialized)
    assert dg.deserialize_value(serialized, RepositorySnap).name == "bar_repo"
