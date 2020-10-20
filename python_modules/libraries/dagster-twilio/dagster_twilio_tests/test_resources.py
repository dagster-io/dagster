import os

import pytest
from dagster import ModeDefinition, execute_solid, solid
from dagster_twilio import twilio_resource
from twilio.base.exceptions import TwilioRestException


def test_twilio_resource():
    account_sid = os.environ.get("TWILIO_TEST_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_TEST_AUTH_TOKEN")

    @solid(required_resource_keys={"twilio"})
    def twilio_solid(context):
        assert context.resources.twilio

        # These tests are against the live SMS APIs using test creds/numbers; see
        # https://www.twilio.com/docs/iam/test-credentials#test-sms-messages

        context.resources.twilio.messages.create(
            body="test message", from_="+15005550006", to="+15005550006"
        )

        with pytest.raises(TwilioRestException) as exc_info:
            context.resources.twilio.messages.create(
                body="test message", from_="+15005550006", to="+15005550001"
            )
        assert "The 'To' number +15005550001 is not a valid phone number" in str(exc_info.value)

    result = execute_solid(
        twilio_solid,
        run_config={
            "resources": {
                "twilio": {"config": {"account_sid": account_sid, "auth_token": auth_token}}
            }
        },
        mode_def=ModeDefinition(resource_defs={"twilio": twilio_resource}),
    )
    assert result.success
