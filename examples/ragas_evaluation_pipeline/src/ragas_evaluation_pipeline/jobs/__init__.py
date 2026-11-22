"""Jobs that materialize the evaluation asset graph.

``evaluation_job`` selects every asset (and their attached asset checks), so the
schedule and the index-refresh sensor both trigger a full evaluation run.
"""

from dagster import AssetSelection, define_asset_job

evaluation_job = define_asset_job(
    "evaluation_job",
    selection=AssetSelection.all(),
)
