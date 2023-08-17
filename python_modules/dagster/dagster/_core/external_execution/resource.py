from typing import Dict, Mapping, Optional, Sequence, Union

from dagster_external.protocol import ExternalExecutionExtras, ExternalExecutionIOMode
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
    input_mode: ExternalExecutionIOMode = Field(default="stdio")
    output_mode: ExternalExecutionIOMode = Field(default="stdio")
    input_path: Optional[str] = Field(
        default=None,
        description="""
        Path to use for output. This can be used in `file`/`fifo` modes to specify a path to a
        temporary file/fifo used to pass information from the orchestration process to the external
        process. If this parameter is not set, the framework will use a file/fifo in a temporary
        directory.

        In both `file` and `fifo` modes, the containing directory must already exist. Any
        preexisting file at the provided path will be overwritten if it already exists, and the
        created file/fifo will be deleted after the external process completes.
        """,
    )
    output_path: Optional[str] = Field(
        default=None,
        description="""
        Path to use for output. This can be used in `file`/`fifo` modes to specify a path to a
        temporary file/fifo used to pass information from the external process to the orchestration
        process. If this parameter is not set, the framework will use a file/fifo in a temporary
        directory.

        In both `file` and `fifo` modes, the containing directory must already exist. Any
        preexisting file at the provided path will be overwritten if it already exists, and the
        created file/fifo will be deleted after the external process completes.
        """,
    )

    def run(
        self,
        command: Union[str, Sequence[str]],
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        return_code = ExternalExecutionTask(
            command=command,
            context=context,
            extras=extras,
            env={**(self.env or {}), **(env or {})},
            input_mode=self.input_mode,
            output_mode=self.output_mode,
            input_path=self.input_path,
            output_path=self.output_path,
        ).run()

        if return_code:
            raise Failure(description="External execution process failed.")
