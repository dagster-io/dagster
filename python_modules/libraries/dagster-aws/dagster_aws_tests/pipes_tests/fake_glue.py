import subprocess
import sys
import tempfile
from typing import Dict, Optional

import boto3


class LocalGlueMockClient:
    def __init__(self, s3_client: boto3.client, glue_client: boto3.client):
        """This class wraps moto3 clients for S3 and Glue, and provides a way to "run" Glue jobs locally.
        This is necessary because moto3 does not actually run anything when you start a Glue job, so we won't be able
        to receive any Dagster messages from it.
        """
        self.s3_client = s3_client
        self.glue_client = glue_client

    def get_job_run(self, *args, **kwargs):
        return self.glue_client.get_job_run(*args, **kwargs)

    def start_job_run(self, JobName: str, Arguments: Optional[Dict[str, str]], *args, **kwargs):
        params = {
            "JobName": JobName,
        }

        if Arguments:
            params["Arguments"] = Arguments  # type: ignore

        script_s3_path = self.glue_client.get_job(JobName=JobName)["Job"]["Command"][
            "ScriptLocation"
        ]
        bucket = script_s3_path.split("/")[2]
        key = "/".join(script_s3_path.split("/")[3:])

        # load the script and execute it locally
        with tempfile.NamedTemporaryFile() as f:
            self.s3_client.download_file(bucket, key, f.name)

            args = []
            for key, val in (Arguments or {}).items():
                args.append(key)
                args.append(val)

            result = subprocess.run(
                [sys.executable, f.name, *args],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # mock the job run with moto
        response = self.glue_client.start_job_run(**params)

        # replace run state with actual results
        response["JobRun"] = {}

        response["JobRun"]["JobRunState"] = "SUCCEEDED" if result.returncode == 0 else "FAILED"

        # add error message if failed
        if result.returncode != 0:
            # this actually has to be just the Python exception, but this is good enough for now
            response["JobRun"]["ErrorMessage"] = result.stderr

        return response
