import os

import pytest
from dagster import op
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_twilio import TwilioResource, twilio_resource
from twilio.base.exceptions import TwilioRestException


@pytest.fixture(name="twilio_resource_option", params=[True, False])
def twilio_resource_option_fixture(request):
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
    def twilio_op(twilio_resource: TwilioResource):
        # These tests are against the live SMS APIs using test creds/numbers; see
        # https://www.twilio.com/docs/iam/test-credentials#test-sms-messages

        twilio = twilio_resource.create_client()
        twilio.messages.create(body="test message", from_="+15005550006", to="+15005550006")

        with pytest.raises(TwilioRestException) as exc_info:
            twilio.messages.create(body="test message", from_="+15005550006", to="+15005550001")
        assert "The 'To' number +15005550001 is not a valid phone number" in str(exc_info.value)

    result = wrap_op_in_graph_and_execute(
        twilio_op,
        resources={
            "twilio_resource": TwilioResource(account_sid=account_sid, auth_token=auth_token)
        },
    )
    assert result.success
