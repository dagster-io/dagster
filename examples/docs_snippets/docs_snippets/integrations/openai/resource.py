# start_example
from dagster_openai import OpenAIResource

from dagster import EnvVar

# Pull API key from environment variables
openai = OpenAIResource(
    api_key=EnvVar("OPENAI_API_KEY"),
)
# end_example
