"""Entrypoint for a step running on EMR on EKS."""
import base64
import json
import os
import pickle
import sys

import boto3
from dagster.core.execution.plan.external_step import run_step_from_ref
from dagster.core.instance import DagsterInstance
from dagster_aws.s3.file_manager import S3FileHandle, S3FileManager
from dagster_aws.emr.pyspark_step_launcher import CODE_ZIP_NAME

# Any event whose JSON representation is larger than this
# will be dropped. Otherwise, it can cause EMR to stop
# reporting all logs to Cloudwatch Logs.
_MAX_EVENT_SIZE_BYTES = 64 * 1024
from dagster_aws.emr.pyspark_step_launcher import CODE_ZIP_NAME


def main(s3_bucket_step_run_ref: str, s3_key_step_run_ref: str) -> None:
    session = boto3.client("s3")

    # This must be called before any of our packages is imported
    # Force the right version of dagstersdk to get imported before
    # Dagster messes with the Python path.
    _adjust_pythonpath_for_staged_assets(os.getenv("ENV_PATHS").split(","))
    print(f"Python path: {sys.path}")

    # Read the step description
    file_manager = S3FileManager(session, s3_bucket_step_run_ref, "")
    file_handle = S3FileHandle(s3_bucket_step_run_ref, s3_key_step_run_ref)

    step_run_ref_data = file_manager.read_data(file_handle)
    step_run_ref = pickle.loads(step_run_ref_data)

    print(f"Running the following step: {step_run_ref}")

    # Run the Dagster job. The plan process should tail the job
    # logs in order to extract events.
    with DagsterInstance.ephemeral() as instance:
        for event in run_step_from_ref(step_run_ref, instance):
            _dump_event(event)

    print("Job is over")


def _adjust_pythonpath_for_staged_assets(code_subpaths=None):
    """Adjust Python path for Python packages in staged code.

    When staging code through S3 instead of using code baked in the
    docker image, packages such as ``dagster-sdk`` are still picked up
    from the docker image by default, as they are not directly in the
    path.

    This function adds Python packages in the staged code to the path
    explicitly so that they are picked up.
    """
    code_subpaths = code_subpaths or []

    code_entries = [
        filename for filename in sys.path if os.path.basename(filename) == CODE_ZIP_NAME
    ]

    if not code_entries:
        print("`code.zip` is not in the Python path, code was not staged")
        return

    code_path = code_entries[0]

    for subpath in code_subpaths:
        path_to_add = os.path.join(code_path, subpath)

        print(f"Adding {path_to_add} to Python path")
        sys.path.insert(0, path_to_add)


def _event_to_str(event):
    """Convert a Dagster event to a string that can be logged."""
    return base64.b64encode(pickle.dumps(event)).decode("ascii")


def _dump_event(event):
    """Dump a Dagster event to ``stdout``."""
    event_json = json.dumps({"event": _event_to_str(event), "eventDescr": str(event)})

    if len(event_json) > _MAX_EVENT_SIZE_BYTES:
        print(f"Dropping event of size {len(event_json)} bytes: '{event_json[:32]}...'")
        return

    print(event_json)


if __name__ == "__main__":
    assert len(sys.argv) == 3
    main(sys.argv[1], sys.argv[2])
