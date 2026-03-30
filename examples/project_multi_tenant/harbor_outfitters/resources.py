from __future__ import annotations

from shared.io_managers import make_duckdb_io_manager
from shared.resources import CatalogCoach, build_llm_resource


def get_resources() -> dict[str, object]:
    return {
        "llm": build_llm_resource(
            CatalogCoach,
            model_env_var="HARBOR_OUTFITTERS_MODEL",
            legacy_model_env_var="TENANT_ALPHA_MODEL",
            default_model_name="qwen2.5:0.5b",
            runtime_dependency_package="catalog_coach_runtime",
        ),
        "io_manager": make_duckdb_io_manager("harbor_outfitters"),
    }
