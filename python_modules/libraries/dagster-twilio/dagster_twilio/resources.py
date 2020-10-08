from twilio.rest import Client

from dagster import Field, StringSource, resource


@resource(
    {
        "account_sid": Field(StringSource, description="Twilio Account SID"),
        "auth_token": Field(StringSource, description="Twilio Auth Token"),
    },
    description="This resource is for connecting to Twilio",
)
def twilio_resource(context):
    return Client(context.resource_config["account_sid"], context.resource_config["auth_token"])
