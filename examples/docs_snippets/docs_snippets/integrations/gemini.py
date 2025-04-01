from dagster_gemini import GeminiResource

import dagster as dg


@dg.asset(compute_kind="gemini")
def gemini_asset(context: dg.AssetExecutionContext, gemini: GeminiResource):
    with gemini.get_model(context) as model:
        response = model.generate_content("Generate a short sentence on tests")


defs = dg.Definitions(
    assets=[gemini_asset],
    resources={
        "gemini": GeminiResource(
            api_key=dg.EnvVar("GEMINI_API_KEY"),
            generative_model_name="gemini-1.5-flash",
        ),
    },
)
