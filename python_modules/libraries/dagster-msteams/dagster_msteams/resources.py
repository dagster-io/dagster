from dagster import Bool, Field, Float, StringSource, resource

from dagster_msteams.client import TeamsClient


@resource(
    {
        "hook_url": Field(
            StringSource,
            description="""To send messages to MS Teams channel, an incoming webhook has to
                    be created. The incoming webhook url must be given as a part of the
                    resource config to the msteams_resource in dagster.
                    """,
        ),
        "http_proxy": Field(StringSource, is_required=False),
        "https_proxy": Field(StringSource, is_required=False),
        "timeout": Field(Float, default_value=60, is_required=False),
        "Verify": Field(Bool, is_required=False),
    },
    description="This resource is for connecting to MS Teams",
)
def msteams_resource(context):
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
    return TeamsClient(
        hook_url=context.resource_config.get("hook_url"),
        http_proxy=context.resource_config.get("http_proxy"),
        https_proxy=context.resource_config.get("https_proxy"),
        timeout=context.resource_config.get("timeout"),
        verify=context.resource_config.get("verify"),
    )
