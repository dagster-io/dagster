from __future__ import annotations

from pathlib import Path

import dagster as dg

from shared.io_managers import make_duckdb_io_manager
from summit_financial import defs
from summit_financial.assets.bronze import raw_accounts, raw_risk_rules, raw_transactions
from summit_financial.assets.gold import (
    account_summary,
    risk_llm_audit_log,
    risk_prompt_inputs,
    transaction_risk_scores,
)
from summit_financial.assets.silver import (
    cleaned_transactions,
    risk_context_documents,
    selected_risk_context,
    transaction_context_windows,
    validated_accounts,
)
from tests.fakes import MockLLMResource


def test_summit_financial_definitions_load() -> None:
    asset_keys = defs.resolve_all_asset_keys()
    assert dg.AssetKey(["summit_financial", "transaction_risk_scores"]) in asset_keys
    assert dg.AssetKey(["summit_financial", "account_summary"]) in asset_keys
    job_names = {job.name for job in defs.resolve_all_job_defs()}
    assert "summit_raw_data_job" in job_names
    assert "summit_context_engineering_job" in job_names
    assert "summit_risk_scoring_job" in job_names
    schedule = defs.resolve_schedule_def("summit_daily_refresh_schedule")
    assert schedule.job_name == "summit_risk_scoring_job"


def test_summit_financial_materializes(tmp_path: Path) -> None:
    result = dg.materialize(
        [
            raw_transactions,
            raw_accounts,
            raw_risk_rules,
            cleaned_transactions,
            validated_accounts,
            transaction_context_windows,
            risk_context_documents,
            selected_risk_context,
            risk_prompt_inputs,
            transaction_risk_scores,
            risk_llm_audit_log,
            account_summary,
        ],
        resources={
            "llm": MockLLMResource(model_name="beta-test"),
            "io_manager": make_duckdb_io_manager("summit_financial_test", base_dir=tmp_path),
        },
    )
    assert result.success
    scores = result.output_for_node("transaction_risk_scores")
    assert {"transaction_id", "risk_level", "score"}.issubset(scores.columns)
    assert set(scores["risk_level"]).issubset({"low", "medium", "high"})
