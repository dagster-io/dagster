import uuid
from http import client
from typing import cast

from dagster_powerbi import PowerBIServicePrincipal, PowerBIToken, PowerBIWorkspace

from dagster import Definitions, EnvVar, asset, define_asset_job

# Connect using a service principal
resource = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=EnvVar("POWER_BI_WORKSPACE_ID"),
)

# Alternatively, connect directly using an API access token
resource = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=EnvVar("POWER_BI_API_TOKEN")),
    workspace_id=EnvVar("POWER_BI_WORKSPACE_ID"),
)

defs = resource.build_defs()
