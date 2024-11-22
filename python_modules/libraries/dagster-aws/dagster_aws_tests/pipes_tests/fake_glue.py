import sys
import tempfile
import time
import warnings
from dataclasses import dataclass
from subprocess import PIPE, Popen
from typing import Dict, List, Literal, Optional

import boto3


@dataclass
class SimulatedJobRun:
    popen: Popen
    job_run_id: str
    log_group: str
    local_script: tempfile._TemporaryFileWrapper
    stopped: bool = False


class LocalGlueMockClient:
    def __init__(
        self,
        aws_endpoint_url: str,  # usually received from moto
        s3_client: boto3.client,  # pyright: ignore (reportGeneralTypeIssues)
        glue_client: boto3.client,  # pyright: ignore (reportGeneralTypeIssues)
        pipes_messages_backend: Literal["s3", "cloudwatch"],
        cloudwatch_client: Optional[boto3.client] = None,  # pyright: ignore (reportGeneralTypeIssues)
    ):
        """This class wraps moto3 clients for S3 and Glue, and provides a way to "run" Glue jobs locally.
        This is necessary because moto3 does not actually run anything when you start a Glue job, so we won't be able
        to receive any Dagster messages from it.
        If pipes_messages_backend is configured to be CloudWatch, it also uploads stderr and stdout logs to CloudWatch
        as if this has been done by Glue.

        Once the job is submitted, it is being executed in a separate process to mimic Glue behavior.
        Once the job status is requested, the process is checked for its status and the result is returned.
        """
        self.aws_endpoint_url = aws_endpoint_url
        self.s3_client = s3_client
        self.glue_client = glue_client
        self.pipes_messages_backend = pipes_messages_backend
        self.cloudwatch_client = cloudwatch_client

        self.process = None  # jobs will be executed in a separate process

        self._job_runs: dict[str, SimulatedJobRun] = {}  # mapping of JobRunId to SimulatedJobRun

    @property
    def meta(self):
        return self.glue_client.meta

    def get_job_run(self, JobName: str, RunId: str):
        # get original response
        response = self.glue_client.get_job_run(JobName=JobName, RunId=RunId)

        # check if status override is set
        simulated_job_run = self._job_runs[RunId]

        if simulated_job_run.stopped:
            response["JobRun"]["JobRunState"] = "STOPPED"
            return response

        # check if popen has completed
        if simulated_job_run.popen.poll() is not None:
            simulated_job_run.popen.wait()
            # check status code
            if simulated_job_run.popen.returncode == 0:
                response["JobRun"]["JobRunState"] = "SUCCEEDED"
            else:
                response["JobRun"]["JobRunState"] = "FAILED"
                _, stderr = simulated_job_run.popen.communicate()
                response["JobRun"]["ErrorMessage"] = stderr.decode()

            # upload logs to cloudwatch
            if self.pipes_messages_backend == "cloudwatch":
                self._upload_logs_to_cloudwatch(RunId)
        else:
            response["JobRun"]["JobRunState"] = "RUNNING"

        return response

    def start_job_run(self, JobName: str, Arguments: Optional[dict[str, str]], **kwargs):
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

        # mock the job run with moto
        response = self.glue_client.start_job_run(**params)
        job_run_id = response["JobRunId"]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f = tempfile.NamedTemporaryFile(
                delete=False
            )  # we will close this file later during garbage collection
        # load the S3 script to a local file
        self.s3_client.download_file(bucket, key, f.name)

        # execute the script in a separate process
        args = []
        for key, val in (Arguments or {}).items():
            args.append(key)
            args.append(val)
        popen = Popen(
            [sys.executable, f.name, *args],
            env={
                "AWS_ENDPOINT_URL": self.aws_endpoint_url,
                "TESTING_PIPES_MESSAGES_BACKEND": self.pipes_messages_backend,
            },
            stdout=PIPE,
            stderr=PIPE,
        )

        # record execution metadata for later use
        self._job_runs[job_run_id] = SimulatedJobRun(
            popen=popen,
            job_run_id=job_run_id,
            log_group=self.glue_client.get_job_run(JobName=JobName, RunId=job_run_id)["JobRun"][
                "LogGroupName"
            ],
            local_script=f,
        )

        return response

    def batch_stop_job_run(self, JobName: str, JobRunIds: list[str]):
        for job_run_id in JobRunIds:
            if simulated_job_run := self._job_runs.get(job_run_id):
                simulated_job_run.popen.terminate()
                simulated_job_run.stopped = True
                self._upload_logs_to_cloudwatch(job_run_id)

    def _upload_logs_to_cloudwatch(self, job_run_id: str):
        log_group = self._job_runs[job_run_id].log_group
        stdout, stderr = self._job_runs[job_run_id].popen.communicate()

        if self.pipes_messages_backend == "cloudwatch":
            assert (
                self.cloudwatch_client is not None
            ), "cloudwatch_client has to be provided with cloudwatch messages backend"

            assert (
                self.cloudwatch_client is not None
            ), "cloudwatch_client has to be provided with cloudwatch messages backend"

            try:
                self.cloudwatch_client.create_log_group(
                    logGroupName=f"{log_group}/output",
                )
            except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                pass

            try:
                self.cloudwatch_client.create_log_stream(
                    logGroupName=f"{log_group}/output",
                    logStreamName=job_run_id,
                )
            except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                pass

            for out in [stderr, stdout]:  # Glue routes both stderr and stdout to /output
                for line in out.decode().split(
                    "\n"
                ):  # uploading log lines one by one is good enough for tests
                    if line:
                        self.cloudwatch_client.put_log_events(
                            logGroupName=f"{log_group}/output",
                            logStreamName=job_run_id,
                            logEvents=[
                                {"timestamp": int(time.time() * 1000), "message": str(line)}
                            ],
                        )
        time.sleep(
            0.01
        )  # make sure the logs will be properly filtered by ms timestamp when accessed next time

    def __del__(self):
        # cleanup local script paths
        for job_run in self._job_runs.values():
            job_run.local_script.close()
