import json
import os

from dagster import Definitions, EnvVar, RunRequest, SensorResult, load_assets_from_modules, sensor
from dagster_aws.s3 import S3PickleIOManager, S3Resource
from dagster_openai import OpenAIResource

from . import assets
from .assets import question_job, search_index_job


@sensor(job=question_job)
def question_sensor(context):
    PATH_TO_QUESTIONS = os.path.join(os.path.dirname(__file__), "../../", "data/questions")

    previous_state = json.loads(context.cursor) if context.cursor else {}
    current_state = {}
    runs_to_request = []

    for filename in os.listdir(PATH_TO_QUESTIONS):
        file_path = os.path.join(PATH_TO_QUESTIONS, filename)
        if filename.endswith(".json") and os.path.isfile(file_path):
            last_modified = os.path.getmtime(file_path)

            current_state[filename] = last_modified

            if filename not in previous_state or previous_state[filename] != last_modified:
                with open(file_path) as f:
                    request_config = json.load(f)

                    runs_to_request.append(
                        RunRequest(
                            run_key=f"adhoc_request_{filename}_{last_modified}",
                            run_config={"ops": {"completion": {"config": {**request_config}}}},
                        )
                    )

    return SensorResult(run_requests=runs_to_request, cursor=json.dumps(current_state))


all_assets = load_assets_from_modules([assets])
all_jobs = [question_job, search_index_job]
all_sensors = [question_sensor]

# for handling passing data between assets in cloud env
io_manager_resource_dict = (
    {
        "io_manager": S3PickleIOManager(
            s3_resource=S3Resource(),
            s3_bucket="with_openai",
        )
    }
    if os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME")
    else {}
)


defs = Definitions(
    assets=all_assets,
    jobs=all_jobs,
    resources={
        "openai": OpenAIResource(api_key=EnvVar("OPENAI_API_KEY")),
        **io_manager_resource_dict,
    },
    sensors=all_sensors,
)
