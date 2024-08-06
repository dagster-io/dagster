import subprocess
import sys
import tempfile
import time
from typing import Dict, Literal, Optional

import boto3


class LocalGlueMockClient:
    def __init__(
        self,
        aws_endpoint_url: str,  # usually received from moto
        s3_client: boto3.client,
        glue_client: boto3.client,
        pipes_messages_backend: Literal["s3", "cloudwatch"],
        cloudwatch_client: Optional[boto3.client] = None,
    ):
        """This class wraps moto3 clients for S3 and Glue, and provides a way to "run" Glue jobs locally.
        This is necessary because moto3 does not actually run anything when you start a Glue job, so we won't be able
        to receive any Dagster messages from it.
        If pipes_messages_backend is configured to be CloudWatch, it also uploads stderr and stdout logs to CloudWatch
        as if this has been done by Glue.
        """
        self.aws_endpoint_url = aws_endpoint_url
        self.s3_client = s3_client
        self.glue_client = glue_client
        self.pipes_messages_backend = pipes_messages_backend
        self.cloudwatch_client = cloudwatch_client

    def get_job_run(self, *args, **kwargs):
        return self.glue_client.get_job_run(*args, **kwargs)

    def start_job_run(self, JobName: str, Arguments: Optional[Dict[str, str]], **kwargs):
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
                env={
                    "AWS_ENDPOINT_URL": self.aws_endpoint_url,
                    "TESTING_PIPES_MESSAGES_BACKEND": self.pipes_messages_backend,
                },
                capture_output=True,
            )

        # mock the job run with moto
        response = self.glue_client.start_job_run(**params)
        job_run_id = response["JobRunId"]

        job_run_response = self.glue_client.get_job_run(JobName=JobName, RunId=job_run_id)
        log_group = job_run_response["JobRun"]["LogGroupName"]

        if self.pipes_messages_backend == "cloudwatch":
            assert (
                self.cloudwatch_client is not None
            ), "cloudwatch_client has to be provided with cloudwatch messages backend"

            self.cloudwatch_client.create_log_group(
                logGroupName=f"{log_group}/output",
            )

            self.cloudwatch_client.create_log_stream(
                logGroupName=f"{log_group}/output",
                logStreamName=job_run_id,
            )

            for line in result.stderr.decode().split(
                "\n"
            ):  # uploading log lines one by one is good enough for tests
                if line:
                    self.cloudwatch_client.put_log_events(
                        logGroupName=f"{log_group}/output",  # yes, Glue routes stderr to /output
                        logStreamName=job_run_id,
                        logEvents=[{"timestamp": int(time.time() * 1000), "message": str(line)}],
                    )
            time.sleep(
                0.01
            )  # make sure the logs will be properly filtered by ms timestamp when accessed next time

        # replace run state with actual results
        response["JobRun"] = {}

        response["JobRun"]["JobRunState"] = "SUCCEEDED" if result.returncode == 0 else "FAILED"

        # add error message if failed
        if result.returncode != 0:
            # this actually has to be just the Python exception, but this is good enough for now
            response["JobRun"]["ErrorMessage"] = result.stderr

        return response
