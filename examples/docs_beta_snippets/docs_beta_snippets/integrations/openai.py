from dagster_openai import OpenAIResource

import dagster as dg


@dg.asset(compute_kind="OpenAI")
def openai_asset(context: dg.AssetExecutionContext, openai: OpenAIResource):
    with openai.get_client(context) as client:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test."}],
        )


openai_asset_job = dg.define_asset_job(
    name="openai_asset_job", selection="openai_asset"
)

defs = dg.Definitions(
    assets=[openai_asset],
    jobs=[openai_asset_job],
    resources={
        "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
    },
)
