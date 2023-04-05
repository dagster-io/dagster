import os

import pytest
from dagster import Resource, op
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_twilio import TwilioResource, twilio_resource
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client


@pytest.fixture(name="twilio_resource_option", params=[True, False])
def twilio_resource_option_fixture(request) -> ResourceDefinition:
    if request.param:
        return twilio_resource
    else:
        return TwilioResource.configure_at_launch()


def test_twilio_resource(twilio_resource_option) -> None:
    account_sid = os.environ.get("TWILIO_TEST_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_TEST_AUTH_TOKEN")

    assert account_sid, "TWILIO_TEST_ACCOUNT_SID not set"
    assert auth_token, "TWILIO_TEST_AUTH_TOKEN not set"

    @op
    def twilio_op(twilio: Resource[Client]):
        # These tests are against the live SMS APIs using test creds/numbers; see
        # https://www.twilio.com/docs/iam/test-credentials#test-sms-messages

        twilio.messages.create(body="test message", from_="+15005550006", to="+15005550006")

        with pytest.raises(TwilioRestException) as exc_info:
            twilio.messages.create(body="test message", from_="+15005550006", to="+15005550001")
        assert "The 'To' number +15005550001 is not a valid phone number" in str(exc_info.value)

    result = wrap_op_in_graph_and_execute(
        twilio_op,
        run_config={
            "resources": {
                "twilio": {"config": {"account_sid": account_sid, "auth_token": auth_token}}
            }
        },
        resources={"twilio": twilio_resource_option},
    )
    assert result.success
