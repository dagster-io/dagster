from typing import Dict, Optional, Sequence, Union

from dagster_external.protocol import ExternalExecutionExtras
from pydantic import Field

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.events import Failure
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.external_execution.task import (
    ExternalExecutionTask,
)


class ExternalExecutionResource(ConfigurableResource):
    env: Optional[Dict[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )
    cwd: Optional[str] = Field(
        default=None, description="Working directory in which to launch the subprocess command."
    )
    input_mode: str = Field(default="stdio")
    output_mode: str = Field(default="stdio")
    input_fifo: Optional[str] = Field(
        default=None,
        description="Path to a pre-existing FIFO to use for input when `input_mode` is `fifo`.",
    )
    output_fifo: Optional[str] = Field(
        default=None,
        description="Path to a pre-existing FIFO to use for output when `output_mode` is `fifo`.",
    )

    def run(
        self,
        command: Union[str, Sequence[str]],
        context: OpExecutionContext,
        extras: ExternalExecutionExtras,
    ) -> None:
        return_code = ExternalExecutionTask(
            command=command,
            context=context,
            extras=extras,
            env=self.env,
            input_mode=self.input_mode,
            output_mode=self.output_mode,
            input_fifo=self.input_fifo,
            output_fifo=self.output_fifo,
        ).run()

        if return_code:
            raise Failure(description="External execution process failed.")
