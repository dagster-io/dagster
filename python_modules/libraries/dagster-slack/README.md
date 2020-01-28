# dagster-slack

##Introduction
This library provides an integration with Slack, to support posting messages in your company's Slack workspace.

Presently, it provides a thin wrapper on the Slack client API [chat.postMessage](https://api.slack.com/methods/chat.postMessage).

## Getting Started

To use this integration, you'll first need to create a Slack App for it.

1. **Create App**: Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click "Create New App":

   <img width=200px src="https://user-images.githubusercontent.com/609349/57993925-d3824800-7a6f-11e9-8618-bdd1611f15a4.png" />

2. **Install App**: After creating an app, on the left-hand side of the app configuration, click "Bot Users", and then create a bot user. Then, click "Install App" on the left hand side, and finally "Install App to Workspace".

3. **Bot Token**: Once finished, this will create a new bot token for your bot/workspace:

   <img width=600px src="https://user-images.githubusercontent.com/609349/57994422-ed248f00-7a71-11e9-9cbc-f6869ed33315.png" />

Copy this bot token and put it somewhere safe; see [Safely Storing Credentials](https://api.slack.com/docs/oauth-safety) for more on this topic.

## Posting Messages

Now, you can easily post messages to Slack from Dagster with the Slack resource:

```python
import os

from dagster import solid, execute_pipeline, ModeDefinition
from dagster_slack import slack_resource


@solid(required_resource_keys={'slack'})
def slack_solid(context):
    context.resources.slack.chat.post_message(channel='#noise', text=':wave: hey there!')

@pipeline(
    mode_defs=[ModeDefinition(resource_defs={'slack': slack_resource})],
)
def slack_pipeline():
    slack_solid()

execute_pipeline(
    slack_pipeline, {'resources': {'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}}}}
)
```

Run the above code, and you'll see the message appear in Slack:

<img src="https://user-images.githubusercontent.com/609349/57994610-c581f680-7a72-11e9-85cd-41fd649cc26d.png" />

By provisioning `slack_resource` as a Dagster pipeline resource, you can post to Slack from within any solid execution.
