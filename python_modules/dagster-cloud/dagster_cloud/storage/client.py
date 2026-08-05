from dagster import (
    Any,
    Array,
    BoolSource,
    Field,
    IntSource,
    Map,
    Noneable,
    Permissive,
    ScalarUnion,
    StringSource,
)
from dagster_cloud_cli.core.graphql_client import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
)


def dagster_cloud_api_config():
    return {
        "url": Field(
            StringSource,
            is_required=False,
            description="Dagster+ API server URL. This can be omitted and is derived from your agent token.",
        ),
        "agent_token": Field(
            StringSource, is_required=True, description="Dagster+ agent api token."
        ),
        "agent_label": Field(
            StringSource,
            is_required=False,
            description="Custom label visible in the Dagster+ UI.",
        ),
        "deployment": Field(
            ScalarUnion(scalar_type=str, non_scalar_schema=Array(str)),
            is_required=False,
            description="Handle requests for a single deployment.",
        ),
        # Handle requests for multiple non-branch deployments
        "deployments": Field(
            Array(StringSource),
            is_required=False,
            description="Handle requests for multiple deployments",
        ),
        # Handle requests for all branch deployments (can be combined with `deployment`)`
        "branch_deployments": Field(
            BoolSource,
            default_value=False,
            is_required=False,
            description="Handle requests for all branch deployments (can be combined with `deployment` or `deployments`)",
        ),
        "timeout": Field(
            Noneable(IntSource),
            default_value=DEFAULT_TIMEOUT,
            description="How long before a request times out against the Dagster+ API servers.",
        ),
        "retries": Field(
            IntSource,
            default_value=DEFAULT_RETRIES,
            description="How many times to retry retriable response codes (429, 503, etc.) before failing.",
        ),
        "backoff_factor": Field(
            float,
            default_value=DEFAULT_BACKOFF_FACTOR,
            description="Exponential factor to back off between retries.",
        ),
        "method": Field(StringSource, default_value="POST", description="Default HTTP method."),
        "verify": Field(bool, default_value=True, description="If False, ignore verifying SSL."),
        "headers": Field(Permissive(), default_value={}, description="Custom headers."),
        "cookies": Field(Permissive(), default_value={}, description="Custom cookies."),
        "proxies": Field(Map(str, str), is_required=False, description="Custom proxies."),
        "socket_options": Field(Noneable(Array(Array(Any))), description="Custom socket options."),
        "all_serverless_deployments": Field(
            BoolSource,
            default_value=False,
            is_required=False,
            description="Unused by hybrid agents",
        ),
    }
