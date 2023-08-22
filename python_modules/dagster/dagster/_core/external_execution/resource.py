from abc import ABC, abstractmethod
from typing import Optional

from dagster_external.protocol import ExternalExecutionExtras
from pydantic import Field

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.execution.context.compute import OpExecutionContext


class ExternalExecutionResource(ConfigurableResource, ABC):
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

    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
    ) -> None:
        ...
