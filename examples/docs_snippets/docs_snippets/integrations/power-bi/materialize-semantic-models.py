import uuid
from typing import cast

from dagster_powerbi import PowerBIServicePrincipal, PowerBIWorkspace

from dagster import Definitions, EnvVar, asset, define_asset_job

resource = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=EnvVar("POWER_BI_WORKSPACE_ID"),
)
defs = resource.build_defs(enable_refresh_semantic_models=True)
