from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, List, Optional, Sequence

from dagster_pipes import (
    PipesContextData,
    PipesExtras,
    PipesParams,
)

from dagster import _check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.result import MaterializeResult
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

    def get_materialize_result(self) -> MaterializeResult:
        mat_results: List[MaterializeResult] = [
            mat_result for mat_result in self._results if isinstance(mat_result, MaterializeResult)
        ]
        check_results: List[AssetCheckResult] = [
            check_result
            for check_result in self._results
            if isinstance(check_result, AssetCheckResult)
        ]

        check.invariant(
            len(mat_results) == 1,
            "Multiple materialize results returned. If this was deliberate, use get_results()"
            " instead.",
        )
        mat_result = next(iter(mat_results))
        for check_result in check_results:
            if check_result.asset_key:
                check.invariant(
                    mat_result.asset_key == check_result.asset_key,
                    "Check result specified an asset key that is not part of the returned"
                    " materialization. If this was deliberate, use get_results() instead.",
                )

        if check_results:
            return mat_result._replace(
                check_results=[*(mat_result.check_results or []), *check_results]
            )
        else:
            return mat_result


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
