# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources
from dagster_twilio import TwilioResource

import dagster as dg


@dg.asset
def twilio_message(twilio: TwilioResource):
    twilio.get_client().messages.create(
        to="+15551234567", from_="+15558901234", body="Hello world!"
    )


defs = dg.Definitions(
    assets=[twilio_message],
    resources={
        "twilio": TwilioResource(
            account_sid=dg.EnvVar("TWILIO_ACCOUNT_SID"),
            auth_token=dg.EnvVar("TWILIO_AUTH_TOKEN"),
        )
    },
)
