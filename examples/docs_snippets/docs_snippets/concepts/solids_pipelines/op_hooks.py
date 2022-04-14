# isort: skip_file
import yaml
from unittest import mock
from dagster_slack import slack_resource
from dagster import (
    ResourceDefinition,
    file_relative_path,
    graph,
    job,
    op,
    repository,
)

# start_repo_marker_0
from dagster import HookContext, failure_hook, success_hook


@success_hook(required_resource_keys={"slack"})
def slack_message_on_success(context: HookContext):
    message = f"Op {context.op.name} finished successfully"
    context.resources.slack.chat.post_message(channel="#foo", text=message)


@failure_hook(required_resource_keys={"slack"})
def slack_message_on_failure(context: HookContext):
    message = f"Op {context.op.name} failed"
    context.resources.slack.chat.post_message(channel="#foo", text=message)


# end_repo_marker_0

slack_resource_mock = mock.MagicMock()


@op
def a():
    pass


@op
def b():
    raise Exception()


# start_repo_marker_1
@job(resource_defs={"slack": slack_resource}, hooks={slack_message_on_failure})
def notif_all():
    # the hook "slack_message_on_failure" is applied on every op instance within this graph
    a()
    b()


# end_repo_marker_1


# start_repo_marker_3
@graph
def slack_notif_all():
    a()
    b()


notif_all_prod = slack_notif_all.to_job(
    name="notif_all_prod",
    resource_defs={
        "slack": ResourceDefinition.hardcoded_resource(
            slack_resource_mock, "do not send messages in dev"
        )
    },
    hooks={slack_message_on_failure},
)

notif_all_dev = slack_notif_all.to_job(
    name="notif_all_dev",
    resource_defs={"slack": slack_resource},
    hooks={slack_message_on_failure},
)


# end_repo_marker_3


# start_repo_marker_2
@job(resource_defs={"slack": slack_resource})
def selective_notif():
    # only op "a" triggers hooks: a slack message will be sent when it fails or succeeds
    a.with_hooks({slack_message_on_failure, slack_message_on_success})()
    # op "b" won't trigger any hooks
    b()


# end_repo_marker_2


@repository
def repo():
    return [notif_all, selective_notif]


# start_repo_main
if __name__ == "__main__":
    with open(
        file_relative_path(__file__, "prod_op_hooks.yaml"),
        "r",
    ) as fd:
        run_config = yaml.safe_load(fd.read())
    result = notif_all_dev.execute_in_process(
        run_config=run_config, raise_on_error=False
    )
# end_repo_main


# start_testing_hooks
from dagster import build_hook_context


@success_hook(required_resource_keys={"my_conn"})
def my_success_hook(context):
    context.resources.my_conn.send("foo")


def test_my_success_hook():
    my_conn = mock.MagicMock()
    # construct HookContext with mocked ``my_conn`` resource.
    context = build_hook_context(resources={"my_conn": my_conn})

    my_success_hook(context)

    assert my_conn.send.call_count == 1


# end_testing_hooks
