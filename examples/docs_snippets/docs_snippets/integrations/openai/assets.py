# start_example
from dagster_openai import OpenAIResource

from dagster import AssetExecutionContext, Definitions, EnvVar, asset, define_asset_job


@asset(compute_kind="OpenAI")
def openai_asset(context: AssetExecutionContext, openai: OpenAIResource):
    with openai.get_client(context) as client:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test."}],
        )


openai_asset_job = define_asset_job(name="openai_asset_job", selection="openai_asset")

defs = Definitions(
    assets=[openai_asset],
    jobs=[openai_asset_job],
    resources={
        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
    },
)
# end_example
