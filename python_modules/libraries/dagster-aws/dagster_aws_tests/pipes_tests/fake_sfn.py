from datetime import datetime
from typing import Any, Optional


class LocalSfnMockClient:
    def __init__(self):
        self.default_dt = datetime(2024, 1, 1, 12, 0, 0)
        self.execution_arn = (
            "arn:aws:states:us-east-1:123456789012:execution:StateMachine:execution-id"
        )
        self.state_machine_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:StateMachine"

    def start_execution(
        self,
        stateMachineArn: str,
        input: Optional[str] = None,  # noqa: A002 # AWS API parameter
        name: Optional[str] = None,
    ) -> dict[str, Any]:
        return {"executionArn": self.execution_arn, "startDate": self.default_dt}

    def describe_execution(self, executionArn: str):
        return {
            "executionArn": self.execution_arn,
            "stateMachineArn": self.state_machine_arn,
            "name": "execution-id",
            "status": "SUCCEEDED",
            "startDate": self.default_dt,
            "input": '{"key": "value"}',
        }

    def stop_execution(self, executionArn: str):
        return {"executionArn": executionArn, "stopDate": self.default_dt}
