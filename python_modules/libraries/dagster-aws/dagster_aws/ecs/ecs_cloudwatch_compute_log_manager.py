import os
from contextlib import contextmanager
from typing import Generator, List

import boto3

import dagster._check as check
from dagster import Field, StringSource
from dagster._core.storage.captured_log_manager import CapturedLogContext
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._serdes import ConfigurableClass, ConfigurableClassData


class EcsCloudwatchComputeLogManager(NoOpComputeLogManager, ConfigurableClass):
    """
    ComputeLogManager that directs dagit to an external Cloudwatch URL to view compute logs rather
    than capturing them directly.  To be used in tandem with the EcsRunLauncher.
    """

    def __init__(self, inst_data=None, project_name="dagster"):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._project_name = check.str_param(project_name, "project_name")
        self.ecs = boto3.client("ecs")
        super().__init__(inst_data)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "project_name": Field(StringSource, is_required=False, default_value="dagster"),
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return EcsCloudwatchComputeLogManager(inst_data=inst_data, **config_value)

    @contextmanager
    def capture_logs(self, log_key: List[str]) -> Generator[CapturedLogContext, None, None]:
        metadata_uri = os.getenv("ECS_CONTAINER_METADATA_URI")
        region = os.getenv("AWS_REGION")
        if not metadata_uri or not region:
            yield CapturedLogContext(log_key=log_key)
            return

        arn_id = metadata_uri.split("/")[-1].split("-")[0]
        base_url = f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}"
        log_group = f"$252Fdocker-compose$252F{self._project_name}"
        log_name = f"{self._project_name}$252Frun$252F{arn_id}"
        yield CapturedLogContext(
            log_key=log_key,
            external_url=f"{base_url}#logsV2:log-groups/log-group/{log_group}/log-events/{log_name}",
        )
