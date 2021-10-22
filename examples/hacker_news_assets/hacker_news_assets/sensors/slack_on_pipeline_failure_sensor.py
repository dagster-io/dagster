import os
from typing import Dict, List

from dagster import SensorDefinition
from dagster.core.definitions.pipeline_definition_definition_sensor import PipelineFailureSensorContext
from dagster_slack import make_slack_on_pipeline_failure_sensor
from hacker_news_assets.utils.slack_message import build_slack_message_blocks


def slack_message_blocks_fn(context: PipelineFailureSensorContext, base_url: str) -> List[Dict]:
    return build_slack_message_blocks(
        title="👎 Pipeline Failure",
        markdown_message=f'Pipeline "{context.pipeline_run.pipeline_name}" failed.',
        pipeline_name=context.pipeline_run.pipeline_name,
        run_id=context.pipeline_run.run_id,
        mode=context.pipeline_run.mode,
        run_page_url=f"{base_url}/instance/runs/{context.pipeline_run.run_id}",
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
