import os
from typing import Dict, List

from dagster import SensorDefinition
from dagster.core.definitions.pipeline_sensor import PipelineFailureSensorContext
from dagster_slack import make_slack_on_pipeline_failure_sensor
from hacker_news.utils.slack_message import build_slack_message_blocks


def slack_message_blocks_fn(context: PipelineFailureSensorContext, base_url: str) -> List[Dict]:
    return build_slack_message_blocks(
        title="👎 Pipeline Failure",
        markdown_message=f'Pipeline "{context.dagster_run.target.name}" failed.',
        pipeline_name=context.dagster_run.target.name,
        run_id=context.dagster_run.run_id,
        mode=context.dagster_run.target.mode,
        run_page_url=f"{base_url}/instance/runs/{context.dagster_run.run_id}",
    )


def make_pipeline_failure_sensor(base_url: str) -> SensorDefinition:
    return make_slack_on_pipeline_failure_sensor(
        channel="#dogfooding-alert",
        slack_token=os.environ.get("SLACK_DAGSTER_ETL_BOT_TOKEN", ""),
        blocks_fn=lambda context: slack_message_blocks_fn(context, base_url),
        pipeline_selection=[
            "download_pipeline",
            "buildkite_activity_pipeline",
            "slack_stats_pipeline",
            "github_community_pipeline",
        ],
    )
