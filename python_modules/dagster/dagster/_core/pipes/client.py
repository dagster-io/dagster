from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional, Sequence

from dagster_pipes import (
    PipesContextData,
    PipesExtras,
    PipesParams,
)

from dagster._annotations import experimental, public
from dagster._core.execution.context.compute import OpExecutionContext

if TYPE_CHECKING:
    from .context import PipesExecutionResult, PipesMessageHandler


@experimental
class PipesClient(ABC):
    """Pipes client base class.

    Pipes clients for specific external environments should subclass this.
    """

    @public
    @abstractmethod
    def run(
        self,
        *,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
    ) -> "PipesClientCompletedInvocation":
        """Synchronously execute an external process with the pipes protocol.

        Args:
            context (OpExecutionContext): The context from the executing op/asset.
            extras (Optional[PipesExtras]): Arbitrary data to pass to the external environment.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """


@experimental
class PipesClientCompletedInvocation:
    def __init__(self, results: Sequence["PipesExecutionResult"]):
        self._results = results

    def get_results(self) -> Sequence["PipesExecutionResult"]:
        return tuple(self._results)


@experimental
class PipesContextInjector(ABC):
    @abstractmethod
    @contextmanager
    def inject_context(self, context_data: "PipesContextData") -> Iterator[PipesParams]:
        """A `@contextmanager` that injects context data into the external process.

        This method should write the context data to a location accessible to the external
        process. It should yield parameters that the external process can use to locate and load the
        context data.

        Args:
            context_data (PipesContextData): The context data to inject.

        Yields:
            PipesParams: A JSON-serializable dict of parameters to be used used by the external
            process to locate and load the injected context data.
        """


@experimental
class PipesMessageReader(ABC):
    @abstractmethod
    @contextmanager
    def read_messages(self, handler: "PipesMessageHandler") -> Iterator[PipesParams]:
        """A `@contextmanager` that reads messages reported by an external process.

        This method should start a thread to continuously read messages from some location
        accessible to the external process. It should yield parameters that the external process
        can use to direct its message output.

        Args:
            handler (PipesMessageHandler): The message handler to use to process messages read from
                the external process.

        Yields:
            PipesParams: A dict of parameters that can be used by the external process to determine
            where to write messages.
        """
