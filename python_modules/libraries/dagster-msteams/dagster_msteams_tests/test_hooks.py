from typing import Any
from unittest.mock import patch

import pytest
from dagster import op
from dagster._core.definitions.decorators.job_decorator import job
from dagster_msteams import MSTeamsResource
from dagster_msteams.hooks import teams_on_failure, teams_on_success
from dagster_msteams.resources import msteams_resource

from dagster_msteams_tests.conftest import LEGACY_WEBHOOK_URL, WEBHOOK_URL

TEST_RUN_ID = "b6497149-0b91-41ea-8a0f-442cb1704172"


class SomeUserException(Exception):
    pass


def my_message_fn(_):
    return "Some custom text"


@op
def pass_op(_):
    pass


@op
def fail_op(_):
    raise SomeUserException()


@pytest.mark.parametrize(
    "webhook_url",
    [
        LEGACY_WEBHOOK_URL,
        WEBHOOK_URL,
    ],
)
def test_failure_hook_with_pythonic_resource(webhook_url: str, snapshot: Any, mock_post_method):
    @job(resource_defs={"msteams": MSTeamsResource(hook_url=webhook_url)})
    def job_def():
        pass_op.with_hooks(hook_defs={teams_on_failure()})()
        pass_op.alias("fail_op_with_hook").with_hooks(hook_defs={teams_on_failure()})()
        fail_op.alias("fail_op_without_hook")()
        fail_op.with_hooks(
            hook_defs={
                teams_on_failure(message_fn=my_message_fn, webserver_base_url="localhost:3000")
            }
        )()

    result = job_def.execute_in_process(
        raise_on_error=False,
        run_id=TEST_RUN_ID,  # Ensure that run id is consistent for snapshot testing
    )
    assert not result.success
    assert mock_post_method.call_count == 1
    snapshot.assert_match(mock_post_method.call_args_list)


@pytest.mark.parametrize(
    "webhook_url",
    [
        LEGACY_WEBHOOK_URL,
        WEBHOOK_URL,
    ],
)
def test_success_hook_with_pythonic_resource(webhook_url: str, snapshot: Any, mock_post_method):
    @job(resource_defs={"msteams": MSTeamsResource(hook_url=webhook_url)})
    def job_def():
        pass_op.with_hooks(hook_defs={teams_on_success()})()
        pass_op.alias("success_solid_with_hook").with_hooks(hook_defs={teams_on_success()})()
        fail_op.alias("success_solid_without_hook")()
        fail_op.with_hooks(
            hook_defs={
                teams_on_success(message_fn=my_message_fn, webserver_base_url="localhost:3000")
            }
        )()

    result = job_def.execute_in_process(
        raise_on_error=False,
        run_id=TEST_RUN_ID,  # Ensure that run id is consistent for snapshot testing
    )
    assert not result.success
    assert mock_post_method.call_count == 2
    snapshot.assert_match(mock_post_method.call_args_list)


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_failure_hook_on_op_instance(mock_teams_post_message):
    @job(resource_defs={"msteams": msteams_resource})
    def job_def():
        pass_op.with_hooks(hook_defs={teams_on_failure()})()
        pass_op.alias("fail_op_with_hook").with_hooks(hook_defs={teams_on_failure()})()
        fail_op.alias("fail_op_without_hook")()
        fail_op.with_hooks(
            hook_defs={
                teams_on_failure(message_fn=my_message_fn, webserver_base_url="localhost:3000")
            }
        )()

    result = job_def.execute_in_process(
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 1


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_success_hook_on_op_instance(mock_teams_post_message):
    @job(resource_defs={"msteams": msteams_resource})
    def job_def():
        pass_op.with_hooks(hook_defs={teams_on_success()})()
        pass_op.alias("success_solid_with_hook").with_hooks(hook_defs={teams_on_success()})()
        fail_op.alias("success_solid_without_hook")()
        fail_op.with_hooks(
            hook_defs={
                teams_on_success(message_fn=my_message_fn, webserver_base_url="localhost:3000")
            }
        )()

    result = job_def.execute_in_process(
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_failure_hook_decorator(mock_teams_post_message):
    @teams_on_failure(webserver_base_url="http://localhost:3000/")
    @job(resource_defs={"msteams": msteams_resource})
    def job_def():
        pass_op()
        fail_op()
        fail_op.alias("another_fail_op")()

    result = job_def.execute_in_process(
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_success_hook_decorator(mock_teams_post_message):
    @teams_on_success(message_fn=my_message_fn, webserver_base_url="http://localhost:3000/")
    @job(resource_defs={"msteams": msteams_resource})
    def job_def():
        pass_op()
        pass_op.alias("another_pass_op")()
        fail_op()

    result = job_def.execute_in_process(
        run_config={"resources": {"msteams": {"config": {"hook_url": "https://some_url_here/"}}}},
        raise_on_error=False,
    )
    assert not result.success
    assert mock_teams_post_message.call_count == 2
