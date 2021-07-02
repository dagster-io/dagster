from dagster import Field, StringSource, resource, Float, Bool

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
    return TeamsClient(
        hook_url=context.resource_config.get("hook_url"),
        http_proxy=context.resource_config.get("http_proxy"),
        https_proxy=context.resource_config.get("https_proxy"),
        timeout=context.resource_config.get("timeout"),
        verify=context.resource_config.get("verify"),
    )
