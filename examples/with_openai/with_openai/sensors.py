import json
import os

from dagster import (
    RunRequest,
    SensorResult,
    sensor,
)

from .jobs import question_job


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
                with open(file_path, "r") as f:
                    request_config = json.load(f)

                    runs_to_request.append(
                        RunRequest(
                            run_key=f"adhoc_request_{filename}_{last_modified}",
                            run_config={"ops": {"completion": {"config": {**request_config}}}},
                        )
                    )

    return SensorResult(run_requests=runs_to_request, cursor=json.dumps(current_state))
