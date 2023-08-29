from abc import ABC, abstractmethod
from typing import Any, Callable, ContextManager, Mapping, Optional

from dagster_externals import (
    DAGSTER_EXTERNALS_ENV_KEYS,
    ExternalExecutionExtras,
    encode_env_var,
)
from typing_extensions import TypeAlias

from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.external_execution.context import ExternalExecutionOrchestrationContext

ExternalExecutionParams: TypeAlias = Mapping[str, Any]
ExternalExecutionContextInjector: TypeAlias = Callable[
    [ExternalExecutionOrchestrationContext], ContextManager[ExternalExecutionParams]
]
ExternalExecutionMessageReader: TypeAlias = Callable[
    [ExternalExecutionOrchestrationContext], ContextManager[ExternalExecutionParams]
]


class ExternalExecutionResource(ConfigurableResource, ABC):
    def get_base_env(self) -> Mapping[str, str]:
        return {DAGSTER_EXTERNALS_ENV_KEYS["is_orchestration_active"]: encode_env_var(True)}

    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[ExternalExecutionExtras] = None,
        context_injector: Optional[ExternalExecutionContextInjector] = None,
        message_reader: Optional[ExternalExecutionMessageReader] = None,
    ) -> None:
        ...
