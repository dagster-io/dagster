"""Tests for auto-deriving Dagster FreshnessPolicy objects from dbt source freshness config.

dbt sources declared with ``freshness.warn_after`` / ``freshness.error_after`` blocks in
``sources.yml`` are surfaced by ``dagster-dbt`` as observable external :py:class:`AssetSpec`
objects with a :py:class:`TimeWindowFreshnessPolicy` derived from that config. See
:py:func:`dagster_dbt.asset_utils.default_freshness_policy_from_dbt_resource_props` for the
pure derivation and :py:func:`dagster_dbt.asset_specs.build_dbt_source_asset_specs` for the
public helper that emits the source specs.
"""

from datetime import timedelta
from typing import Any

from dagster import AssetSpec, FreshnessPolicy
from dagster._core.definitions.freshness import CronFreshnessPolicy, TimeWindowFreshnessPolicy
from dagster_dbt.asset_specs import build_dbt_asset_specs, build_dbt_source_asset_specs
from dagster_dbt.asset_utils import default_freshness_policy_from_dbt_resource_props
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings


def test_source_specs_no_freshness_policy_by_default_backcompat(
    test_dbt_source_freshness_manifest: dict[str, Any],
) -> None:
    """Backward compatibility: the default translator does NOT derive freshness policies.
    Existing users see no behavior change on upgrade — they must opt in with
    ``enable_source_freshness_policies=True`` to get freshness policies on source assets.
    """
    source_specs = build_dbt_source_asset_specs(manifest=test_dbt_source_freshness_manifest)
    assert source_specs, "fixture is expected to declare at least one source asset"
    assert all(spec.freshness_policy is None for spec in source_specs)


def test_source_specs_include_freshness_policy_when_enabled(
    test_dbt_source_freshness_manifest: dict[str, Any],
) -> None:
    """The fixture project declares warn_after=12h, error_after=24h on a source. When
    ``enable_source_freshness_policies=True`` is set, ``build_dbt_source_asset_specs``
    emits a spec for that source with the derived ``TimeWindowFreshnessPolicy`` attached.
    """
    translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_source_freshness_policies=True)
    )
    source_specs = build_dbt_source_asset_specs(
        manifest=test_dbt_source_freshness_manifest,
        dagster_dbt_translator=translator,
    )
    assert source_specs, "fixture is expected to declare at least one source asset"

    for spec in source_specs:
        assert isinstance(spec, AssetSpec)
        policy = spec.freshness_policy
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(hours=24)
        assert policy.warn_window is not None
        assert policy.warn_window.to_timedelta() == timedelta(hours=12)


def test_source_freshness_policies_can_be_disabled_via_translator_setting(
    test_dbt_source_freshness_manifest: dict[str, Any],
) -> None:
    """Explicitly disabling ``enable_source_freshness_policies=False`` suppresses the
    derivation (redundant with the default but useful to assert behavior).
    """
    translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_source_freshness_policies=False)
    )
    source_specs = build_dbt_source_asset_specs(
        manifest=test_dbt_source_freshness_manifest,
        dagster_dbt_translator=translator,
    )
    assert source_specs
    assert all(spec.freshness_policy is None for spec in source_specs)


def test_model_specs_have_no_freshness_policy_by_default(
    test_dbt_source_freshness_manifest: dict[str, Any],
) -> None:
    """The default derivation only fires for sources. Model asset specs should still have
    ``freshness_policy=None`` unless the user overrides ``get_freshness_policy`` in a
    translator subclass.
    """
    model_specs = build_dbt_asset_specs(manifest=test_dbt_source_freshness_manifest)
    assert model_specs
    assert all(spec.freshness_policy is None for spec in model_specs)


class TestDefaultFreshnessPolicyFromDbtResourceProps:
    """Unit tests for the pure derivation function, independent of the manifest fixture."""

    def _source(self, freshness: dict[str, Any] | None) -> dict[str, Any]:
        return {"resource_type": "source", "freshness": freshness}

    def test_error_after_hours_and_warn_after_hours(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._source(
                {
                    "warn_after": {"count": 6, "period": "hour"},
                    "error_after": {"count": 12, "period": "hour"},
                }
            )
        )
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(hours=12)
        assert policy.warn_window is not None
        assert policy.warn_window.to_timedelta() == timedelta(hours=6)

    def test_error_after_days_no_warn(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._source({"error_after": {"count": 2, "period": "day"}})
        )
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(days=2)
        assert policy.warn_window is None

    def test_error_after_minutes(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._source({"error_after": {"count": 15, "period": "minute"}})
        )
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(minutes=15)

    def test_warn_only_returns_none(self) -> None:
        # dbt allows warn_after without error_after; Dagster requires a fail_window,
        # so we drop the policy rather than fabricate one.
        assert (
            default_freshness_policy_from_dbt_resource_props(
                self._source({"warn_after": {"count": 6, "period": "hour"}})
            )
            is None
        )

    def test_warn_greater_than_error_drops_warn(self) -> None:
        # Invalid combination on dbt's side; degrade gracefully to a fail-only policy
        # rather than raising, so partially misconfigured sources still yield a usable policy.
        policy = default_freshness_policy_from_dbt_resource_props(
            self._source(
                {
                    "warn_after": {"count": 48, "period": "hour"},
                    "error_after": {"count": 24, "period": "hour"},
                }
            )
        )
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(hours=24)
        assert policy.warn_window is None

    def test_unknown_period_returns_none(self) -> None:
        assert (
            default_freshness_policy_from_dbt_resource_props(
                self._source({"error_after": {"count": 1, "period": "week"}})
            )
            is None
        )

    def test_no_freshness_block_returns_none(self) -> None:
        assert default_freshness_policy_from_dbt_resource_props(self._source(None)) is None

    def test_non_source_resource_returns_none(self) -> None:
        model_props = {
            "resource_type": "model",
            "freshness": {
                "error_after": {"count": 12, "period": "hour"},
            },
        }
        assert default_freshness_policy_from_dbt_resource_props(model_props) is None

    def test_returned_policy_is_freshness_policy_subtype(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._source({"error_after": {"count": 1, "period": "hour"}})
        )
        assert isinstance(policy, FreshnessPolicy)


class TestMetaDagsterFreshnessPolicy:
    """Tests for the ``meta.dagster.freshness_policy`` override that takes precedence over
    the ``sources.freshness`` auto-derivation and applies to any resource type (sources,
    models, seeds, snapshots).
    """

    def _with_meta(
        self, resource_type: str, meta_policy: dict[str, Any], **extra: Any
    ) -> dict[str, Any]:
        return {
            "resource_type": resource_type,
            "meta": {"dagster": {"freshness_policy": meta_policy}},
            **extra,
        }

    def test_time_window_policy_on_model(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._with_meta(
                "model",
                {
                    "type": "time_window",
                    "fail_window_seconds": 3600,
                    "warn_window_seconds": 1800,
                },
            )
        )
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(hours=1)
        assert policy.warn_window is not None
        assert policy.warn_window.to_timedelta() == timedelta(minutes=30)

    def test_time_window_policy_fail_only(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._with_meta("model", {"type": "time_window", "fail_window_seconds": 7200})
        )
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(hours=2)
        assert policy.warn_window is None

    def test_cron_policy(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._with_meta(
                "model",
                {
                    "type": "cron",
                    "deadline_cron": "0 8 * * *",
                    "lower_bound_delta_seconds": 3600,
                    "timezone": "America/New_York",
                },
            )
        )
        assert isinstance(policy, CronFreshnessPolicy)
        assert policy.deadline_cron == "0 8 * * *"
        assert policy.lower_bound_delta == timedelta(hours=1)
        assert policy.timezone == "America/New_York"

    def test_cron_policy_defaults_utc_timezone(self) -> None:
        policy = default_freshness_policy_from_dbt_resource_props(
            self._with_meta(
                "model",
                {
                    "type": "cron",
                    "deadline_cron": "0 8 * * *",
                    "lower_bound_delta_seconds": 3600,
                },
            )
        )
        assert isinstance(policy, CronFreshnessPolicy)
        assert policy.timezone == "UTC"

    def test_meta_dagster_overrides_native_source_freshness(self) -> None:
        # Both meta.dagster.freshness_policy AND sources.freshness are set; the meta
        # config wins because it's the explicit user opt-in.
        props = {
            "resource_type": "source",
            "freshness": {"error_after": {"count": 24, "period": "hour"}},
            "meta": {
                "dagster": {
                    "freshness_policy": {
                        "type": "time_window",
                        "fail_window_seconds": 300,  # 5min — very different from 24h
                    }
                }
            },
        }
        policy = default_freshness_policy_from_dbt_resource_props(props)
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window.to_timedelta() == timedelta(minutes=5)

    def test_unknown_type_returns_none(self) -> None:
        assert (
            default_freshness_policy_from_dbt_resource_props(
                self._with_meta("model", {"type": "made-up", "fail_window_seconds": 3600})
            )
            is None
        )

    def test_time_window_missing_fail_window_returns_none(self) -> None:
        assert (
            default_freshness_policy_from_dbt_resource_props(
                self._with_meta("model", {"type": "time_window", "warn_window_seconds": 3600})
            )
            is None
        )

    def test_cron_missing_deadline_returns_none(self) -> None:
        assert (
            default_freshness_policy_from_dbt_resource_props(
                self._with_meta("model", {"type": "cron", "lower_bound_delta_seconds": 3600})
            )
            is None
        )

    def test_non_mapping_meta_freshness_returns_none(self) -> None:
        # Guard against dbt YAML weirdness where meta.dagster.freshness_policy is a
        # string or list rather than a mapping. Silent skip rather than raise.
        props = {
            "resource_type": "model",
            "meta": {"dagster": {"freshness_policy": "0 8 * * *"}},
        }
        assert default_freshness_policy_from_dbt_resource_props(props) is None
