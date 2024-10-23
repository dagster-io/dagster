import uuid
from http import client
from typing import cast

from dagster_powerbi import PowerBIServicePrincipal, PowerBIToken, PowerBIWorkspace

import dagster as dg

# Connect using a service principal
resource = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

# Alternatively, connect directly using an API access token
resource = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=dg.EnvVar("POWER_BI_API_TOKEN")),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

defs = resource.build_defs()
