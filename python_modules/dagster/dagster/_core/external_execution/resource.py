from abc import ABC, abstractmethod
from typing import Optional

from dagster_externals import ExternalExecutionExtras

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.execution.context.compute import OpExecutionContext


class ExternalExecutionResource(ConfigurableResource, ABC):
    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
    ) -> None:
        ...
