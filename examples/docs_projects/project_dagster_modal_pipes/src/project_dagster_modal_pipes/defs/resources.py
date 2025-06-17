from pathlib import Path

import dagster as dg
from dagster_aws.s3 import S3Resource
from dagster_modal import ModalClient
from dagster_openai import OpenAIResource


# start_resources
@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "s3": S3Resource(
                endpoint_url=dg.EnvVar("CLOUDFLARE_R2_API"),
                aws_access_key_id=dg.EnvVar("CLOUDFLARE_R2_ACCESS_KEY_ID"),
                aws_secret_access_key=dg.EnvVar("CLOUDFLARE_R2_SECRET_ACCESS_KEY"),
                region_name="auto",
            ),
            "modal": ModalClient(
                project_directory=Path(__file__).parent.parent.parent.parent
                / "src"
                / "modal_project"
            ),
            "openai": OpenAIResource(api_key=dg.EnvVar("OPENAI_API_KEY")),
        }
    )


# end_resources
