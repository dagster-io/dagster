import logging
import os
from functools import cached_property
from typing import TYPE_CHECKING, Optional

import boto3
from botocore.exceptions import ClientError
from dagster import (
    Field,
    StringSource,
    _check as check,
)
from dagster._core.instance import T_DagsterInstance
from dagster._core.launcher.base import (
    CheckRunHealthResult,
    LaunchRunContext,
    RunLauncher,
    WorkerStatus,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._serdes import ConfigurableClass
from dagster._utils.backoff import backoff
from mypy_boto3_stepfunctions.type_defs import StartExecutionInputRequestTypeDef

if TYPE_CHECKING:
    from dagster._serdes.config_class import ConfigurableClassData
    from mypy_boto3_stepfunctions import SFNClient
    from mypy_boto3_stepfunctions.type_defs import (
        DescribeExecutionOutputTypeDef,
        StopExecutionOutputTypeDef,
    )


DEFAULT_RUN_TASK_RETRIES = 3


class SFNLauncher(RunLauncher[T_DagsterInstance], ConfigurableClass):
    def __init__(
        self,
        inst_data: Optional["ConfigurableClassData"],
        sfn_arn: str,
        name: Optional[str] = None,
        input: Optional[str] = None,  # noqa: A002
        trace_header: Optional[str] = None,
    ) -> None:
        self._client: SFNClient = boto3.client("stepfunctions")
        self._inst_data = inst_data
        self._sfn_arn = check.str_param(sfn_arn, "sfn_arn")
        self._name = check.opt_str_param(name, "name") if name is not None else None
        self._input = check.opt_str_param(input, "input") if name is not None else None
        self._trace_header = (
            check.opt_str_param(trace_header, "trace_header") if trace_header is not None else None
        )

    @cached_property
    def _start_execution_input(self) -> StartExecutionInputRequestTypeDef:
        input_dict: StartExecutionInputRequestTypeDef = {"stateMachineArn": self._sfn_arn}
        if self._name is not None:
            input_dict["name"] = self._name
        if self._input is not None:
            input_dict["input"] = self._input
        if self._trace_header is not None:
            input_dict["traceHeader"] = self._trace_header
        return input_dict

    def launch_run(self, context: LaunchRunContext) -> None:
        try:
            self._execution_arn = self._client.start_execution(**self._start_execution_input)[
                "executionArn"
            ]
        except ClientError as err:
            error_info = err.response.get("Error", {})
            logging.error(
                "Couldn't start execution %s. Here's why: %s: %s",
                self._sfn_arn,
                error_info.get("Code", "Unknown error"),
                error_info.get("Message", "No error message available"),
            )
            raise

    def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
        response = backoff(
            self._describe_execution,
            retry_on=(ClientError,),
            kwargs={"execution_arn": self._execution_arn},
            max_retries=int(
                os.getenv("RUN_TASK_RETRIES", DEFAULT_RUN_TASK_RETRIES),
            ),
        )
        logging.info(
            f"Execution {self._execution_arn} completed successfully, Status: {response['status']}"
        )
        if response["status"] == "SUCCEEDED":
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        elif response["status"] in "RUNNING":
            return CheckRunHealthResult(WorkerStatus.RUNNING)
        elif response["status"] in "FAILED":
            return CheckRunHealthResult(WorkerStatus.FAILED, response.get("error"))
        elif response["status"] in "TIMED_OUT":
            return CheckRunHealthResult(WorkerStatus.FAILED, "Execution timed out.")
        elif response["status"] in "ABORTED":
            return CheckRunHealthResult(WorkerStatus.FAILED, "Execution abourted.")
        return CheckRunHealthResult(WorkerStatus.UNKNOWN)

    def _stop_execution(self, execution_arn: str) -> "StopExecutionOutputTypeDef":
        logging.info(f"Terminating execution {execution_arn}")
        try:
            response = self._client.stop_execution(executionArn=execution_arn)
        except ClientError as err:
            logging.error(f"Couldn't terminate execution {execution_arn}. Here's why: {err}")
            raise
        else:
            logging.info(
                f"Execution {execution_arn} terminated, Stop execution response: {response}"
            )
            return response

    def terminate(self, run_id):
        check.not_implemented("Termination not supported.")

    def _describe_execution(self, execution_arn: str) -> "DescribeExecutionOutputTypeDef":
        try:
            response = self._client.describe_execution(executionArn=execution_arn)
        except ClientError as err:
            logging.error(f"Couldn't describe execution {execution_arn}. Here's why: {err}")
            raise
        else:
            return response

    @property
    def inst_data(self) -> Optional["ConfigurableClassData"]:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "sfn_arn": Field(StringSource, is_required=True),
            "name": Field(StringSource, is_required=False),
            "input": Field(StringSource, is_required=False),
            "trace_header": Field(StringSource, is_required=False),
        }

    @classmethod
    def from_config_value(cls, inst_data: Optional["ConfigurableClassData"], config_value):
        return cls(inst_data=inst_data, **config_value)
