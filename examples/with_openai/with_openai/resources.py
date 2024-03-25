from dagster import EnvVar
from dagster_openai import OpenAIResource

openai_resource = OpenAIResource(api_key=EnvVar("OPENAI_API_KEY"))
