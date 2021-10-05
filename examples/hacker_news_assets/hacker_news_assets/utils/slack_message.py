from typing import Dict, List


def build_slack_message_blocks(
    title: str, markdown_message: str, pipeline_name: str, run_id: str, mode: str, run_page_url: str
) -> List[Dict]:
    """
    A helper method to build visually rich Slack message block, primarily used for Slack alerts.
    See details in https://api.slack.com/reference/block-kit/blocks

    Args:
        title (str): The title of the message block.
        markdown_message (str): The main body of block in markdown format.
        pipeline_name (str): The name of the pipeline.
        run_id (str): The run id of the pipeline.
        mode (str): The mode of the pipeline.
        run_page_url (str): the Dagit url the message.

    Returns:
        List[Dict]: Slack layout blocks.
    """
    return [
        {"type": "header", "text": {"type": "plain_text", "text": title}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{markdown_message}"}},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Pipeline: {pipeline_name}",
                },
                {"type": "mrkdwn", "text": f"Run ID: {run_id}"},
                {"type": "mrkdwn", "text": f"Mode: {mode}"},
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":dagster:  Go To Pipeline Run",
                        "emoji": True,
                    },
                    "url": run_page_url,
                },
            ],
        },
    ]
