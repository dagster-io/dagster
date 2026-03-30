from __future__ import annotations

from shared.io_managers import make_duckdb_io_manager
from shared.resources import BriefingWriter, build_llm_resource


def get_resources() -> dict[str, object]:
    return {
        "llm": build_llm_resource(
            BriefingWriter,
            model_env_var="BEACON_HQ_MODEL",
            legacy_model_env_var="TENANT_GAMMA_MODEL",
            default_model_name="qwen2.5:0.5b",
            runtime_dependency_package="briefing_writer_runtime",
        ),
        "io_manager": make_duckdb_io_manager("beacon_hq"),
    }
