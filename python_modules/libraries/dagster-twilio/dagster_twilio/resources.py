from twilio.rest import Client

from dagster import Field, resource


class TwilioClient(Client):
    def __init__(self, account_sid, auth_token):
        super(TwilioClient, self).__init__(account_sid, auth_token)


@resource(
    {
        'account_sid': Field(str, description='Twilio Account SID'),
        'auth_token': Field(str, description='Twilio Auth Token'),
    },
    description='This resource is for connecting to Slack',
)
def twilio_resource(context):
    return TwilioClient(**context.resource_config)
