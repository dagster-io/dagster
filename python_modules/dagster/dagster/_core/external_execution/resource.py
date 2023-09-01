from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Mapping, Optional

from dagster_externals import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionExtras,
    ExternalExecutionParams,
    encode_env_var,
)

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.execution.context.compute import OpExecutionContext

if TYPE_CHECKING:
    from dagster._core.external_execution.context import ExternalExecutionOrchestrationContext


class ExternalExecutionResource(ConfigurableResource, ABC):
    def get_base_env(self) -> Mapping[str, str]:
        return {DAGSTER_EXTERNALS_ENV_KEYS["is_orchestration_active"]: encode_env_var(True)}

    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
        context_injector: Optional["ExternalExecutionContextInjector"] = None,
        message_reader: Optional["ExternalExecutionMessageReader"] = None,
    ) -> None:
        ...


class ExternalExecutionContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(
        self, context: "ExternalExecutionOrchestrationContext"
    ) -> Iterator[ExternalExecutionParams]:
        ...


class ExternalExecutionMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(
        self, context: "ExternalExecutionOrchestrationContext"
    ) -> Iterator[ExternalExecutionParams]:
        ...
