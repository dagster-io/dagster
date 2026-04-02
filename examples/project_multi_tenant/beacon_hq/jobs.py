from __future__ import annotations

import dagster as dg


beacon_reporting_inputs_job = dg.define_asset_job(
    name="beacon_reporting_inputs_job",
    selection=dg.AssetSelection.assets(
        dg.AssetKey(["beacon_hq", "consolidated_revenue"]),
        dg.AssetKey(["beacon_hq", "risk_overview"]),
        dg.AssetKey(["beacon_hq", "briefing_highlights"]),
    ),
    description="Build Beacon HQ's derived reporting inputs from cross-business revenue and risk signals.",
)

beacon_executive_briefing_job = dg.define_asset_job(
    name="beacon_executive_briefing_job",
    selection=dg.AssetSelection.assets(
        dg.AssetKey(["beacon_hq", "briefing_highlights"]),
        dg.AssetKey(["beacon_hq", "executive_context_packet"]),
        dg.AssetKey(["beacon_hq", "executive_summary"]),
        dg.AssetKey(["beacon_hq", "executive_llm_audit_log"]),
    ),
    description="Produce Beacon HQ's executive briefing and audit log from the prepared reporting context.",
)
