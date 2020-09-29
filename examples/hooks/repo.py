import yaml
from dagster_slack import slack_resource

from dagster import (
    ModeDefinition,
    ResourceDefinition,
    execute_pipeline,
    failure_hook,
    file_relative_path,
    pipeline,
    repository,
    solid,
    success_hook,
)
from dagster.seven import mock

slack_resource_mock = mock.MagicMock()


# start_repo_marker_0
@success_hook(required_resource_keys={"slack"})
def slack_on_success(context):
    message = "Solid {} finished successfully".format(context.solid.name)
    context.resources.slack.chat.post_message(channel="#foo", text=message)


@failure_hook(required_resource_keys={"slack"})
def slack_on_failure(context):
    message = "Solid {} failed".format(context.solid.name)
    context.resources.slack.chat.post_message(channel="#foo", text=message)


# end_repo_marker_0


@solid
def a(_):
    pass


@solid
def b(_):
    raise Exception()


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
# start_repo_marker_1


@slack_on_failure
@pipeline(mode_defs=mode_defs)
def notif_all():
    # the hook "slack_on_failure" is applied on every solid instance within this pipeline
    a()
    b()


# end_repo_marker_1


@pipeline(mode_defs=mode_defs)
def selective_notif():
    # only solid "a" triggers hooks: a slack message will be sent when it fails or succeeds
    a.with_hooks({slack_on_failure, slack_on_success})()
    # solid "b" won't trigger any hooks
    b()


@repository
def repo():
    return [notif_all, selective_notif]


if __name__ == "__main__":
    with open(file_relative_path(__file__, "prod.yaml"), "r",) as fd:
        run_config = yaml.safe_load(fd.read())
    result = execute_pipeline(notif_all, run_config=run_config, mode="prod")
