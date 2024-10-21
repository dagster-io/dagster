import uuid
from typing import cast

from dagster_powerbi import PowerBIServicePrincipal, PowerBIWorkspace

import dagster as dg

resource = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

defs = resource.build_defs(enable_refresh_semantic_models=True)
