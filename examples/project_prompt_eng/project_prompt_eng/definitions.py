import dagster as dg
import project_prompt_eng.assets as assets
from project_prompt_eng.resources import NRELResource
from dagster_anthropic import AnthropicResource


all_assets = dg.load_assets_from_modules([assets])


defs = dg.Definitions(
    assets = all_assets,
    resources = {
        "nrel": NRELResource(api_key=dg.EnvVar("NREL_API_KEY")),
        "anthropic": AnthropicResource(api_key=dg.EnvVar("ANTHROPIC_API_KEY"))
    }
)
