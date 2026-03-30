from __future__ import annotations

import dagster as dg


summit_raw_data_job = dg.define_asset_job(
    name="summit_raw_data_job",
    selection=dg.AssetSelection.groups("bronze"),
    description="Ingest the raw financial transactions, account data, and risk rules for Summit Financial.",
)

summit_context_engineering_job = dg.define_asset_job(
    name="summit_context_engineering_job",
    selection=dg.AssetSelection.assets(
        ["summit_financial", "selected_risk_context"],
        ["summit_financial", "risk_prompt_inputs"],
    ).upstream(),
    description="Assemble investigation context and prompt inputs for Summit Financial's risk review workflow.",
)

summit_risk_scoring_job = dg.define_asset_job(
    name="summit_risk_scoring_job",
    selection=dg.AssetSelection.assets(
        ["summit_financial", "transaction_risk_scores"],
        ["summit_financial", "risk_llm_audit_log"],
        ["summit_financial", "account_summary"],
    ).upstream(),
    description="Run the full Summit Financial risk scoring pipeline from raw transactions to account summaries.",
)
