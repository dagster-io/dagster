from __future__ import annotations

import dagster as dg


harbor_raw_data_job = dg.define_asset_job(
    name="harbor_raw_data_job",
    selection=dg.AssetSelection.groups("bronze"),
    description="Ingest the raw retail source tables and reference context for Harbor Outfitters.",
)

harbor_context_engineering_job = dg.define_asset_job(
    name="harbor_context_engineering_job",
    selection=dg.AssetSelection.assets(
        ["harbor_outfitters", "selected_catalog_context"],
        ["harbor_outfitters", "catalog_prompt_inputs"],
    ).upstream(),
    description="Build Harbor Outfitters' curated catalog context and prompt inputs from upstream source data.",
)

harbor_catalog_publish_job = dg.define_asset_job(
    name="harbor_catalog_publish_job",
    selection=dg.AssetSelection.assets(
        ["harbor_outfitters", "enriched_products"],
        ["harbor_outfitters", "catalog_llm_audit_log"],
        ["harbor_outfitters", "sales_summary"],
    ).upstream(),
    description="Run the full Harbor Outfitters retail publishing pipeline through enrichment and sales outputs.",
)
