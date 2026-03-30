from __future__ import annotations

from shared.io_managers import make_duckdb_io_manager
from shared.resources import RiskReviewer, build_llm_resource


def get_resources() -> dict[str, object]:
    return {
        "llm": build_llm_resource(
            RiskReviewer,
            model_env_var="SUMMIT_FINANCIAL_MODEL",
            legacy_model_env_var="TENANT_BETA_MODEL",
            default_model_name="qwen2.5:1.5b",
            runtime_dependency_package="risk_reviewer_runtime",
        ),
        "io_manager": make_duckdb_io_manager("summit_financial"),
    }
