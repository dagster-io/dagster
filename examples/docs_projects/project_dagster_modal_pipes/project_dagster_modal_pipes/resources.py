from pathlib import Path

import dagster as dg
from dagster_aws.s3 import S3Resource
from dagster_modal import ModalClient
from dagster_openai import OpenAIResource

modal_resource = ModalClient(project_directory=Path(__file__).parent.parent)

openai_resource = OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY"))

s3_resource = S3Resource(
    endpoint_url=dg.EnvVar("CLOUDFLARE_R2_API"),
    aws_access_key_id=dg.EnvVar("CLOUDFLARE_R2_ACCESS_KEY_ID"),
    aws_secret_access_key=dg.EnvVar("CLOUDFLARE_R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)
