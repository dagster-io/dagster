"""Dagster entry point — wires assets, checks, jobs, schedules, sensors, resources.

Dagster discovers the whole example through the ``defs`` object exported here:

    dagster dev -m ragas_evaluation_pipeline.definitions

Keeping everything wired in one place makes the pipeline reproducible and the
release-gate policy auditable.
"""

import os

from dagster import Definitions, load_assets_from_modules

from ragas_evaluation_pipeline.assets import pipeline
from ragas_evaluation_pipeline.checks import regression_checks, threshold_checks
from ragas_evaluation_pipeline.jobs import evaluation_job
from ragas_evaluation_pipeline.resources.runtime_metadata_resource import RuntimeMetadataResource
from ragas_evaluation_pipeline.schedules import evaluation_daily_schedule
from ragas_evaluation_pipeline.sensors import index_refresh_sensor

defs = Definitions(
    assets=load_assets_from_modules([pipeline]),
    asset_checks=[
        *threshold_checks.threshold_checks,
        *regression_checks.regression_checks,
    ],
    jobs=[evaluation_job],
    schedules=[evaluation_daily_schedule],
    sensors=[index_refresh_sensor],
    resources={
        # Toggle scoring backend without editing code:
        #   deterministic (default) — offline, no key
        #   ragas — real RAGAS faithfulness via Groq; needs $GROQ_API_KEY
        # Switch with:  $env:RAGAS_SCORER = "ragas"
        "runtime_metadata": RuntimeMetadataResource(
            scorer=os.environ.get("RAGAS_SCORER", "deterministic")
        ),
    },
)
