# start_example
from dagster_openai import OpenAIResource

from dagster import Definitions, EnvVar, GraphDefinition, OpExecutionContext, op


@op
def openai_op(context: OpExecutionContext, openai: OpenAIResource):
    with openai.get_client(context) as client:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say this is a test"}],
        )


openai_op_job = GraphDefinition(name="openai_op_job", node_defs=[openai_op]).to_job()

defs = Definitions(
    jobs=[openai_op_job],
    resources={
        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
    },
)
# end_example
