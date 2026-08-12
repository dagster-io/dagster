"""Tests for the ``enable_code_version_automation`` opt-in that attaches
``AutomationCondition.code_version_changed()`` to dbt model specs.

When enabled, Dagster's automation-tick loop rebuilds a model after any deploy that
changes its SQL body — the ``code_version`` set by ``default_code_version_fn``
(SHA1 of ``raw_sql``) drives the condition. Combines with any existing
``meta.dagster.auto_materialize_policy`` on the model via OR.
"""

from typing import Any

from dagster import AutoMaterializePolicy, AutomationCondition
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, DagsterDbtTranslatorSettings


def _model_props(
    with_auto_materialize_policy: bool = False,
) -> dict[str, Any]:
    props: dict[str, Any] = {
        "resource_type": "model",
        "name": "my_model",
        "raw_sql": "select 1 as id",
        "config": {"materialized": "table"},
        "meta": {},
        "tags": [],
    }
    if with_auto_materialize_policy:
        props["meta"] = {"dagster": {"auto_materialize_policy": {"type": "eager"}}}
    return props


def _source_props() -> dict[str, Any]:
    return {
        "resource_type": "source",
        "source_name": "jaffle",
        "name": "raw",
        "config": {},
        "meta": {},
        "tags": [],
    }


def test_default_translator_does_not_attach_code_version_condition() -> None:
    translator = DagsterDbtTranslator()  # setting defaults to False
    assert translator.get_automation_condition(_model_props()) is None


def test_enabled_flag_attaches_code_version_changed_on_models() -> None:
    translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_version_automation=True)
    )
    condition = translator.get_automation_condition(_model_props())
    assert condition is not None
    assert condition == AutomationCondition.code_version_changed()


def test_enabled_flag_does_not_attach_to_sources() -> None:
    # code_version_changed doesn't make sense for external observable sources —
    # they aren't materialized by dbt so their raw_sql doesn't drive rebuilds.
    translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_version_automation=True)
    )
    assert translator.get_automation_condition(_source_props()) is None


def test_enabled_flag_does_not_attach_to_seeds_or_snapshots() -> None:
    # Seeds and snapshots have their own build semantics separate from SQL changes.
    translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_version_automation=True)
    )
    for resource_type in ("seed", "snapshot"):
        props = {
            "resource_type": resource_type,
            "name": "x",
            "config": {},
            "meta": {},
            "tags": [],
        }
        assert translator.get_automation_condition(props) is None


def test_enabled_flag_combines_with_existing_auto_materialize_policy() -> None:
    # A model with an explicit meta.dagster.auto_materialize_policy should keep it AND
    # get code_version_changed OR-combined so opting in globally doesn't nuke per-model
    # user config.
    translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_version_automation=True)
    )
    condition = translator.get_automation_condition(_model_props(with_auto_materialize_policy=True))
    assert condition is not None
    expected = (
        AutoMaterializePolicy.eager().to_automation_condition()
        | AutomationCondition.code_version_changed()
    )
    assert condition == expected


def test_disabled_flag_preserves_existing_auto_materialize_policy() -> None:
    # With the flag off, existing meta.dagster.auto_materialize_policy still flows through.
    translator = DagsterDbtTranslator()  # default settings
    condition = translator.get_automation_condition(_model_props(with_auto_materialize_policy=True))
    assert condition == AutoMaterializePolicy.eager().to_automation_condition()
