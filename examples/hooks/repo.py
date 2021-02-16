"""isort:skip_file"""
import yaml
from unittest import mock
from dagster_slack import slack_resource
from dagster import (
    ModeDefinition,
    ResourceDefinition,
    execute_pipeline,
    file_relative_path,
    pipeline,
    repository,
    solid,
)

# start_repo_marker_0
from dagster import HookContext, failure_hook, success_hook


@success_hook(required_resource_keys={"slack"})
def slack_message_on_success(context: HookContext):
    message = f"Solid {context.solid.name} finished successfully"
    context.resources.slack.chat.post_message(channel="#foo", text=message)


@failure_hook(required_resource_keys={"slack"})
def slack_message_on_failure(context: HookContext):
    message = f"Solid {context.solid.name} failed"
    context.resources.slack.chat.post_message(channel="#foo", text=message)


# end_repo_marker_0

slack_resource_mock = mock.MagicMock()


@solid
def a(_):
    pass


@solid
def b(_):
    raise Exception()


# start_repo_marker_3
mode_defs = [
    ModeDefinition(
        "dev",
        resource_defs={
            "slack": ResourceDefinition.hardcoded_resource(
                slack_resource_mock, "do not send messages in dev"
            )
        },
    ),
    ModeDefinition("prod", resource_defs={"slack": slack_resource}),
]
# end_repo_marker_3

# start_repo_marker_1
@slack_message_on_failure
@pipeline(mode_defs=mode_defs)
def notif_all():
    # the hook "slack_message_on_failure" is applied on every solid instance within this pipeline
    a()
    b()


# end_repo_marker_1

# start_repo_marker_2
@pipeline(mode_defs=mode_defs)
def selective_notif():
    # only solid "a" triggers hooks: a slack message will be sent when it fails or succeeds
    a.with_hooks({slack_message_on_failure, slack_message_on_success})()
    # solid "b" won't trigger any hooks
    b()


# end_repo_marker_2


@repository
def repo():
    return [notif_all, selective_notif]


if __name__ == "__main__":
    # start_repo_main
    with open(
        file_relative_path(__file__, "prod.yaml"),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    result = execute_pipeline(notif_all, run_config=run_config, mode="prod")
    # end_repo_main
