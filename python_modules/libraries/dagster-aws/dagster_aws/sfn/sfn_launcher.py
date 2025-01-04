import logging
import time
from functools import cached_property
from typing import TYPE_CHECKING, Optional

import boto3
from botocore.exceptions import ClientError
from dagster import (
    Field,
    StringSource,
    _check as check,
)
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.instance import T_DagsterInstance
from dagster._core.launcher.base import LaunchRunContext, RunLauncher
from dagster._serdes import ConfigurableClass
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_fixed

if TYPE_CHECKING:
    from dagster._serdes.config_class import ConfigurableClassData
    from mypy_boto3_stepfunctions import SFNClient
    from mypy_boto3_stepfunctions.type_defs import (
        DescribeExecutionOutputTypeDef,
        StartExecutionInputRequestTypeDef,
        StopExecutionOutputTypeDef,
    )


SFN_FINISHED_STATUSES = ["FAILED", "SUCCEEDED", "TIMED_OUT", "ABORTED"]


class SFNFinishedExecutioinError(Exception):
    pass


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
    def _start_execution_input(self) -> "StartExecutionInputRequestTypeDef":
        input_dict: "StartExecutionInputRequestTypeDef" = {"stateMachineArn": self._sfn_arn}
        if self._name is not None:
            input_dict["name"] = self._name
        if self._input is not None:
            input_dict["input"] = self._input
        if self._trace_header is not None:
            input_dict["traceHeader"] = self._trace_header
        return input_dict

    def launch_run(self, context: LaunchRunContext) -> None:
        try:
            execution_arn = self._client.start_execution(**self._start_execution_input)[
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

        try:
            response = self._wait_for_execution_completion(execution_arn)
        except DagsterExecutionInterruptedError as e:
            logging.error(f"Error waiting for execution completion: {e}")
            _ = self._stop_execution(execution_arn)
            raise
        else:
            logging.info(
                f"Execution {execution_arn} completed successfully, Status: {response['status']}"
            )
            if response["status"] != "SUCCEEDED":
                raise SFNFinishedExecutioinError(
                    f"Step Function execution {self._sfn_arn} run {execution_arn} completed with status {response['status']} :\n{response.get('errorMessage')}",
                )

    @retry(
        retry=retry_if_exception_type(ClientError),
        stop=stop_after_delay(5),
        wait=wait_fixed(5),
    )
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

    def _wait_for_execution_completion(
        self, execution_arn: str
    ) -> "DescribeExecutionOutputTypeDef":
        while True:
            response = self._describe_execution(execution_arn)
            if response["status"] in SFN_FINISHED_STATUSES:
                return response
            time.sleep(5)

    @retry(
        retry=retry_if_exception_type(ClientError),
        stop=stop_after_delay(5),
        wait=wait_fixed(5),
    )
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
