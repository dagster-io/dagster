from typing import Optional

from dagster import ConfigurableResource, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field

from dagster_msteams.client import TeamsClient


class MSTeamsResource(ConfigurableResource):
    """This resource is for connecting to Microsoft Teams.

    Provides a `dagster_msteams.TeamsClient` which can be used to
    interface with the MS Teams API.

    By configuring this resource, you can post messages to MS Teams from any Dagster op,
    asset, schedule, or sensor:

    Examples:
        .. code-block:: python

            import os

            from dagster import op, job, Definitions, EnvVar
            from dagster_msteams import Card, MSTeamsResource


            @op
            def teams_op(msteams: MSTeamsResource):
                card = Card()
                card.add_attachment(text_message="Hello There !!")
                msteams.get_client().post_message(payload=card.payload)


            @job
            def teams_job():
                teams_op()

            defs = Definitions(
                jobs=[teams_job],
                resources={
                    "msteams": MSTeamsResource(
                        hook_url=EnvVar("TEAMS_WEBHOOK_URL")
                    )
                }
            )
    """

    hook_url: str = Field(
        description=(
            "To send messages to MS Teams channel, an incoming webhook has to be created. The"
            " incoming webhook url must be given as a part of the resource config to the"
            " MSTeamsResource in Dagster. For more information on how to create an incoming"
            " webhook, see"
            " https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook"
        ),
    )
    http_proxy: Optional[str] = Field(default=None, description="HTTP proxy URL")
    https_proxy: Optional[str] = Field(default=None, description="HTTPS proxy URL")
    timeout: float = Field(default=60, description="Timeout for requests to MS Teams")
    verify: bool = Field(
        default=True, description="Whether to verify SSL certificates, defaults to True"
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_client(self) -> TeamsClient:
        return TeamsClient(
            hook_url=self.hook_url,
            http_proxy=self.http_proxy,
            https_proxy=self.https_proxy,
            timeout=self.timeout,
            verify=self.verify,
        )


@dagster_maintained_resource
@resource(
    config_schema=MSTeamsResource.to_config_schema(),
    description="This resource is for connecting to MS Teams",
)
def msteams_resource(context) -> TeamsClient:
    """This resource is for connecting to Microsoft Teams.

    The resource object is a `dagster_msteams.TeamsClient`.

    By configuring this resource, you can post messages to MS Teams from any Dagster solid:

    Examples:
        .. code-block:: python

            import os

            from dagster import op, job
            from dagster_msteams import Card, msteams_resource


            @op(required_resource_keys={"msteams"})
            def teams_op(context):
                card = Card()
                card.add_attachment(text_message="Hello There !!")
                context.resources.msteams.post_message(payload=card.payload)


            @job(resource_defs={"msteams": msteams_resource})
            def teams_job():
                teams_op()


            teams_job.execute_in_process(
                {"resources": {"msteams": {"config": {"hook_url": os.getenv("TEAMS_WEBHOOK_URL")}}}}
            )
    """
    return MSTeamsResource.from_resource_context(context).get_client()
