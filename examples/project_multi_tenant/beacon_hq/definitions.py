from __future__ import annotations

import dagster as dg

from beacon_hq.assets import reports
from beacon_hq.jobs import beacon_executive_briefing_job, beacon_reporting_inputs_job
from beacon_hq.sensors import beacon_after_upstream_success_sensor
from shared.io_managers import make_duckdb_io_manager
from shared.resources import BriefingWriter, build_llm_resource


defs = dg.Definitions(
    assets=dg.load_assets_from_modules(
        [reports],
        key_prefix=["beacon_hq"],
    ),
    jobs=[
        beacon_reporting_inputs_job,
        beacon_executive_briefing_job,
    ],
    resources={
        "llm": build_llm_resource(
            BriefingWriter,
            model_env_var="BEACON_HQ_MODEL",
            legacy_model_env_var="TENANT_GAMMA_MODEL",
            default_model_name="qwen2.5:0.5b",
            runtime_dependency_package="briefing_writer_runtime",
        ),
        "io_manager": make_duckdb_io_manager("beacon_hq"),
    },
    sensors=[beacon_after_upstream_success_sensor],
)
