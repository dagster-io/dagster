from dagster_anthropic import AnthropicResource

import dagster as dg


@dg.asset(compute_kind="anthropic")
def anthropic_asset(context: dg.AssetExecutionContext, anthropic: AnthropicResource):
    with anthropic.get_client(context) as client:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Say this is a test"}],
        )


defs = dg.Definitions(
    assets=[anthropic_asset],
    resources={
        "anthropic": AnthropicResource(api_key=dg.EnvVar("ANTHROPIC_API_KEY")),
    },
)
