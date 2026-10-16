from collections.abc import Mapping, Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest
from dagster._core.errors import DagsterInvalidConfigError
from dagster_azure.container_apps.container_context import AcaContainerContext


def _ctx(
    *,
    env_vars: Sequence[str] | None = None,
    run_resources: Mapping[str, Any] | None = None,
    server_resources: Mapping[str, Any] | None = None,
    identity_id: str | None = None,
    run_job_replica_timeout: int | None = None,
) -> AcaContainerContext:
    """Test helper: construct a context with defaults so cases stay readable.

    Exempt from the no-default-params rule as a test helper whose purpose is
    to reduce boilerplate at call sites under a strict keyword-only
    constructor.
    """
    return AcaContainerContext(
        env_vars=env_vars,
        run_resources=run_resources,
        server_resources=server_resources,
        identity_id=identity_id,
        run_job_replica_timeout=run_job_replica_timeout,
    )


class TestMerge:
    def test_env_vars_dedupe_identical_entries(self):
        base = _ctx(env_vars=["A=1", "B=2"])
        other = _ctx(env_vars=["A=1", "C=3"])
        merged = base.merge(other)
        # Identical strings collapse; order follows `other` first (mirrors ECS).
        assert list(merged.env_vars) == ["A=1", "C=3", "B=2"]

    def test_env_vars_conflicting_values_resolved_at_dict_time(self):
        # A=1 and A=2 are distinct strings; dedupe keeps both in the list.
        # get_environment_dict() collapses by key; last key wins (self wins).
        base = _ctx(env_vars=["A=2"])
        other = _ctx(env_vars=["A=1"])
        merged = base.merge(other)
        assert list(merged.env_vars) == ["A=1", "A=2"]
        assert merged.get_environment_dict() == {"A": "2"}

    def test_run_resources_other_overrides(self):
        base = _ctx(run_resources={"cpu": "0.5", "memory": "1Gi"})
        other = _ctx(run_resources={"cpu": "1"})
        merged = base.merge(other)
        assert merged.run_resources == {"cpu": "1", "memory": "1Gi"}

    def test_server_resources_other_overrides(self):
        base = _ctx(server_resources={"cpu": "0.5", "memory": "1Gi"})
        other = _ctx(server_resources={"memory": "2Gi"})
        merged = base.merge(other)
        assert merged.server_resources == {"cpu": "0.5", "memory": "2Gi"}

    def test_scalar_fields_other_wins_when_set(self):
        base = _ctx(identity_id="self-id")
        other = _ctx(identity_id="other-id")
        merged = base.merge(other)
        assert merged.identity_id == "other-id"

    def test_scalar_fields_self_wins_when_other_unset(self):
        base = _ctx(identity_id="self-id")
        other = _ctx()
        merged = base.merge(other)
        assert merged.identity_id == "self-id"

    def test_run_job_replica_timeout_other_wins_when_set(self):
        base = _ctx(run_job_replica_timeout=3600)
        other = _ctx(run_job_replica_timeout=7200)
        merged = base.merge(other)
        assert merged.run_job_replica_timeout == 7200

    def test_run_job_replica_timeout_self_wins_when_other_unset(self):
        base = _ctx(run_job_replica_timeout=3600)
        other = _ctx()
        merged = base.merge(other)
        assert merged.run_job_replica_timeout == 3600

    def test_empty_merge_is_identity(self):
        base = _ctx(env_vars=["A=1"], run_resources={"cpu": "1"})
        merged = base.merge(AcaContainerContext.empty())
        assert list(merged.env_vars) == ["A=1"]
        assert merged.run_resources == {"cpu": "1"}


class TestGetEnvironmentDict:
    def test_literal_kv(self):
        ctx = _ctx(env_vars=["FOO=bar", "BAZ=qux"])
        assert ctx.get_environment_dict() == {"FOO": "bar", "BAZ": "qux"}

    def test_bare_key_pulls_from_process_env(self, monkeypatch):
        monkeypatch.setenv("PULLED_FROM_ENV", "hello")
        ctx = _ctx(env_vars=["PULLED_FROM_ENV"])
        assert ctx.get_environment_dict() == {"PULLED_FROM_ENV": "hello"}

    def test_last_entry_wins_for_duplicate_keys(self):
        ctx = _ctx(env_vars=["A=1", "A=2"])
        assert ctx.get_environment_dict() == {"A": "2"}


class TestCreateFromConfig:
    def test_empty_returns_bare_context(self):
        ctx = AcaContainerContext.create_from_config({})
        assert list(ctx.env_vars) == []
        assert ctx.run_resources == {}

    def test_shared_env_vars_propagate(self):
        ctx = AcaContainerContext.create_from_config({"env_vars": ["SHARED=1"]})
        assert list(ctx.env_vars) == ["SHARED=1"]

    def test_aca_block_overrides_and_extends(self):
        ctx = AcaContainerContext.create_from_config(
            {
                "env_vars": ["SHARED=1"],
                "aca": {
                    "env_vars": ["ACA=2"],
                    "run_resources": {"cpu": "0.5", "memory": "1Gi"},
                    "identity_id": "my-id",
                },
            }
        )
        # Shared vars + ACA-block vars both present, deduped.
        assert set(ctx.env_vars) == {"SHARED=1", "ACA=2"}
        assert ctx.run_resources == {"cpu": "0.5", "memory": "1Gi"}
        assert ctx.identity_id == "my-id"


class TestEmpty:
    def test_empty_is_merge_identity(self):
        e = AcaContainerContext.empty()
        assert list(e.env_vars) == []
        assert e.run_resources == {}
        assert e.identity_id is None


class TestCreateForRun:
    def _run(self, container_context):
        run = MagicMock()
        run.job_code_origin.repository_origin.container_context = container_context
        return run

    def test_no_launcher_and_no_origin_is_empty(self):
        run = MagicMock()
        run.job_code_origin = None
        assert AcaContainerContext.create_for_run(run, None) == AcaContainerContext.empty()

    def test_launcher_settings_alone(self):
        launcher = MagicMock(
            env_vars=["A=1"],
            run_resources={"cpu": "1"},
            identity_id="id",
            run_job_replica_timeout=5,
        )
        ctx = AcaContainerContext.create_for_run(self._run({}), launcher)
        assert list(ctx.env_vars) == ["A=1"]
        assert ctx.run_resources == {"cpu": "1"}
        assert ctx.identity_id == "id"
        assert ctx.run_job_replica_timeout == 5

    def test_location_settings_layer_over_launcher(self):
        launcher = MagicMock(
            env_vars=["A=1"],
            run_resources={"cpu": "1", "memory": "1Gi"},
            identity_id="id",
            run_job_replica_timeout=5,
        )
        run = self._run(
            {
                "aca": {
                    "env_vars": ["B=2"],
                    "run_resources": {"memory": "4Gi"},
                    "run_job_replica_timeout": 9,
                }
            }
        )
        ctx = AcaContainerContext.create_for_run(run, launcher)
        assert set(ctx.env_vars) == {"A=1", "B=2"}
        assert ctx.run_resources == {"cpu": "1", "memory": "4Gi"}
        assert ctx.identity_id == "id"
        assert ctx.run_job_replica_timeout == 9


class TestCreateFromConfigErrors:
    @pytest.mark.parametrize(
        "aca_block",
        [
            {"run_resources": {"cpu": 5}},
            {"run_job_replica_timeout": "soon"},
            {"identity_id": 123},
            {"env_vars": "NOT_A_LIST"},
            {"unknown_key": True},
        ],
    )
    def test_invalid_aca_block_raises(self, aca_block):
        with pytest.raises(DagsterInvalidConfigError):
            AcaContainerContext.create_from_config({"aca": aca_block})
