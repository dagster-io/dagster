import dagster as dg
import project_prompt_eng.assets as assets
from project_prompt_eng.resources import NRELResource
from dagster_openai import OpenAIResource


all_assets = dg.load_assets_from_modules([assets])


defs = dg.Definitions.merge(
    assets = all_assets,
    resources = {
        "nrel": NRELResource(api_key=dg.EnvVar("NREL_API_KEY")),
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY"))
    }
)
