from __future__ import annotations

from pathlib import Path

import dagster as dg

from shared.io_managers import make_duckdb_io_manager
from harbor_outfitters import defs
from harbor_outfitters.assets.bronze import (
    raw_brand_guidelines,
    raw_products,
    raw_sales,
    raw_taxonomy_examples,
)
from harbor_outfitters.assets.gold import catalog_llm_audit_log, enriched_products, sales_summary
from harbor_outfitters.assets.silver import (
    catalog_context_documents,
    catalog_prompt_inputs,
    cleaned_sales,
    selected_catalog_context,
    standardized_products,
)
from tests.fakes import MockLLMResource


def test_harbor_outfitters_definitions_load() -> None:
    asset_keys = defs.resolve_all_asset_keys()
    assert dg.AssetKey(["harbor_outfitters", "enriched_products"]) in asset_keys
    assert dg.AssetKey(["harbor_outfitters", "sales_summary"]) in asset_keys
    job_names = {job.name for job in defs.resolve_all_job_defs()}
    assert "harbor_raw_data_job" in job_names
    assert "harbor_context_engineering_job" in job_names
    assert "harbor_catalog_publish_job" in job_names
    schedule = defs.resolve_schedule_def("harbor_daily_refresh_schedule")
    assert schedule.job_name == "harbor_catalog_publish_job"


def test_harbor_outfitters_materializes(tmp_path: Path) -> None:
    result = dg.materialize(
        [
            raw_sales,
            raw_products,
            raw_brand_guidelines,
            raw_taxonomy_examples,
            cleaned_sales,
            standardized_products,
            catalog_context_documents,
            selected_catalog_context,
            catalog_prompt_inputs,
            enriched_products,
            catalog_llm_audit_log,
            sales_summary,
        ],
        resources={
            "llm": MockLLMResource(model_name="alpha-test"),
            "io_manager": make_duckdb_io_manager("harbor_outfitters_test", base_dir=tmp_path),
        },
    )
    assert result.success
    summary = result.output_for_node("sales_summary")
    assert not summary.empty
