import uuid
from typing import cast

from dagster_powerbi import PowerBIWorkspace

from dagster import Definitions, EnvVar, asset, define_asset_job

resource = PowerBIWorkspace(
    api_token=EnvVar("POWER_BI_API_TOKEN"),
    workspace_id=EnvVar("POWER_BI_WORKSPACE_ID"),
)
powerbi_definitions = resource.build_defs()

defs = Definitions.merge(powerbi_definitions)
