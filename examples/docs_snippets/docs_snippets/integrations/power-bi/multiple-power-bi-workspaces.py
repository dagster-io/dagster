import uuid
from http import client
from typing import cast

from dagster_powerbi import PowerBIServicePrincipal, PowerBIToken, PowerBIWorkspace

from dagster import Definitions, EnvVar, asset, define_asset_job

credentials = PowerBIServicePrincipal(
    client_id=EnvVar("POWER_BI_CLIENT_ID"),
    client_secret=EnvVar("POWER_BI_CLIENT_SECRET"),
    tenant_id=EnvVar("POWER_BI_TENANT_ID"),
)

sales_team_workspace = PowerBIWorkspace(
    credentials=credentials,
    workspace_id="726c94ff-c408-4f43-8edf-61fbfa1753c7",
)

marketing_team_workspace = PowerBIWorkspace(
    credentials=credentials,
    workspace_id="8b7f815d-4e64-40dd-993c-cfa4fb12edee",
)

defs = Definitions.merge(
    sales_team_workspace.build_defs(),
    marketing_team_workspace.build_defs(),
)
