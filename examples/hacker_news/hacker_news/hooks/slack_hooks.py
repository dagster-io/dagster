from dagster import HookContext, success_hook
from hacker_news.utils.slack_message import build_slack_message_blocks


@success_hook(required_resource_keys={"slack", "base_url"})
def slack_on_success(context: HookContext):
    run_page_url = f"{context.resources.base_url}/instance/runs/{context.run_id}?logs=query%3A{context.step_key}&selection={context.step_key}"

    channel = "#dogfooding-alert"
    message_blocks = build_slack_message_blocks(
        title="👍 Solid Success",
        markdown_message=f'Solid "{context.solid.name}" Succeeded.',
        pipeline_name=context.pipeline_name,
        run_id=context.run_id,
        mode=context.mode_def.name,
        run_page_url=run_page_url,
    )
    context.log.info(f'Sending slack message to {channel}: "{message_blocks}"')

    context.resources.slack.chat_postMessage(
        channel=channel,
        blocks=message_blocks,
    )
