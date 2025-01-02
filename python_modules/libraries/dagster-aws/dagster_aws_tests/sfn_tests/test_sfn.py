import os
import time
from functools import partial
from threading import Thread
from typing import TYPE_CHECKING

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_stepfunctions

from dagster_aws.sfn.sfn_launcher import SFNFinishedExecutioinError, SFNLauncher

if TYPE_CHECKING:
    from mypy_boto3_stepfunctions import SFNClient


class SFNController(Thread):
    def __init__(self, sfn_arn, stub_launch_context):
        super().__init__(daemon=True)
        self.sfn_launcher = SFNLauncher.from_config_value(None, {"sfn_arn": sfn_arn})
        self._stub_launch_context = stub_launch_context

    def run(self):
        self.sfn_launcher.launch_run(self._stub_launch_context)


@mock_stepfunctions
def test_launch_run(stub_launch_context):
    sfn_client: "SFNClient" = boto3.client("stepfunctions")
    sfn_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:TestSFN"
    wrong_sfn_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:WrongTestSFN"
    sfn_client.create_state_machine(
        name="TestSFN",
        definition='{"StartAt": "HelloWorld","States": {"HelloWorld": {"Type": "Task","Resource": "arn:aws:states:::lambda:invoke","End": true}}}',
        roleArn="arn:aws:iam::123456789012:role/service-role/StatesExecutionRole-us-east-1",
    )
    os.environ["SF_EXECUTION_HISTORY_TYPE"] = (
        "FAILURE"  # (moto design) SF_EXECUTION_HISTORY_TYPE has 2 possible values: "SUCCESS" and "FAILURE", FAILURE returns FAILED status, SUCCESS - RUNNING
    )
    sfn_launcher = SFNLauncher.from_config_value(None, {"sfn_arn": sfn_arn})
    with pytest.raises(SFNFinishedExecutioinError):
        sfn_launcher.launch_run(stub_launch_context)
    os.environ["SF_EXECUTION_HISTORY_TYPE"] = "SUCCESS"
    sfn_launcher = SFNLauncher.from_config_value(None, {"sfn_arn": wrong_sfn_arn})
    with pytest.raises(ClientError):
        sfn_launcher.launch_run(stub_launch_context)
    sfn_launcher = SFNLauncher.from_config_value(None, {"sfn_arn": sfn_arn})
    target = partial(sfn_launcher.launch_run, stub_launch_context)
    sfn_cont = Thread(target=target, daemon=True)
    sfn_cont.start()
    time.sleep(5)
    assert sfn_cont.is_alive()
