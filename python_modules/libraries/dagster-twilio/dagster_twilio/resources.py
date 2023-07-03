from dagster import ConfigurableResource, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.init import InitResourceContext
from pydantic import Field
from twilio.rest import Client


class TwilioResource(ConfigurableResource):
    """This resource is for connecting to Twilio."""

    account_sid: str = Field(
        description=(
            "Twilio Account SID, created with yout Twilio account. This can be found on your Twilio"
            " dashboard, see"
            " https://www.twilio.com/blog/twilio-access-tokens-python"
        ),
    )
    auth_token: str = Field(
        description=(
            "Twilio Authentication Token, created with yout Twilio account. This can be found on"
            " your Twilio dashboard, see https://www.twilio.com/blog/twilio-access-tokens-python"
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def create_client(self) -> Client:
        return Client(self.account_sid, self.auth_token)


@dagster_maintained_resource
@resource(
    config_schema=TwilioResource.to_config_schema(),
    description="This resource is for connecting to Twilio",
)
def twilio_resource(context: InitResourceContext) -> Client:
    return TwilioResource.from_resource_context(context).create_client()
