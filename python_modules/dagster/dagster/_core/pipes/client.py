from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Sequence

from dagster_pipes import (
    DagsterPipesError,
    PipesContextData,
    PipesExtras,
    PipesOpenedData,
    PipesParams,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.pipes.context import PipesExecutionResult, PipesSession

if TYPE_CHECKING:
    from dagster._core.pipes.context import PipesMessageHandler


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
        **kwargs,
    ) -> "PipesClientCompletedInvocation":
        """Synchronously execute an external process with the pipes protocol. Derived
         clients must have `context` and `extras` arguments, but also can add arbitrary
         arguments that are appropriate for their own implementation.

        Args:
            context (OpExecutionContext): The context from the executing op/asset.
            extras (Optional[PipesExtras]): Arbitrary data to pass to the external environment.

        Returns:
            PipesClientCompletedInvocation: Wrapper containing results reported by the external
            process.
        """


class PipesClientCompletedInvocation:
    """A wrapper for the results of a pipes client invocation, typically returned from `PipesClient.run`.

    Args:
        session (PipesSession): The Pipes session that was used to run the external process.
        metadata (Optional[Dict[str, Any]]): Arbitrary metadata attached to the invocation,
            such as an external job_id or other information available on the client side.
            Do not confuse with Dagster metadata logged in the external process.
    """

    def __init__(
        self,
        session: PipesSession,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self._session = session
        self._metadata = metadata or {}

    @property
    def metadata(self) -> Dict[str, Any]:
        """Arbitrary metadata attached to the invocation."""
        return self._metadata

    def get_results(
        self,
        *,
        implicit_materializations=True,
    ) -> Sequence["PipesExecutionResult"]:
        """Get the stream of results as a Sequence of a completed pipes
        client invocation.

        Args:
            implicit_materializations (bool): Create MaterializeResults for expected assets
                even if nothing was reported from the external process.


        Returns: Sequence[PipesExecutionResult]
        """
        return self._session.get_results(implicit_materializations=implicit_materializations)

    def get_materialize_result(
        self,
        *,
        implicit_materialization=True,
    ) -> MaterializeResult:
        """Get a single materialize result for a pipes invocation. This coalesces
        the materialization result and any separately reported asset check results from
        the external process.

        This does not work on invocations that materialize multiple assets and will fail
        in that case. For multiple assets use `get_results` instead to get the result stream.

        Args:
            implicit_materializations (bool): Create MaterializeResults for expected asset
                even if nothing was reported from the external process.


        Returns: MaterializeResult
        """
        return materialize_result_from_pipes_results(
            self.get_results(implicit_materializations=implicit_materialization)
        )

    def get_asset_check_result(self) -> AssetCheckResult:
        """Get a single asset check result for a pipes invocation.

        This does not work on invocations that have anything except a single asset check result.
        Use `get_results` instead to get the result stream in those cases.

        Returns: AssetCheckResult
        """
        return _check_result_from_pipes_results(self.get_results())

    def get_custom_messages(self) -> Sequence[Any]:
        """Get the sequence of deserialized JSON data that was reported from the external process using
        `report_custom_message`.

        Returns: Sequence[Any]
        """
        return self._session.get_custom_messages()


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

    @abstractmethod
    def no_messages_debug_text(self) -> str:
        """A message to be displayed when no messages are received from the external process to aid with debugging.

        Example: "Attempted to inject context using a magic portal. Expected PipesMagicPortalContextLoader to be
        explicitly passed to open_dagster_pipes in the external process."
        """


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

    def on_opened(self, opened_payload: PipesOpenedData) -> None:
        """Hook called when the external process has successfully launched and returned an opened
        payload.

        By default this is a no-op. Specific message readers can override this to action information
        that can only be obtained from the external process.
        """

    @abstractmethod
    def no_messages_debug_text(self) -> str:
        """A message to be displayed when no messages are received from the external process to aid with
        debugging.

        Example: "Attempted to read messages using a magic portal. Expected PipesMagicPortalMessageWriter
        to be explicitly passed to open_dagster_pipes in the external process."
        """


def materialize_result_from_pipes_results(
    all_results: Sequence[PipesExecutionResult],
) -> MaterializeResult:
    mat_results: List[MaterializeResult] = [
        mat_result for mat_result in all_results if isinstance(mat_result, MaterializeResult)
    ]
    check_results: List[AssetCheckResult] = [
        check_result for check_result in all_results if isinstance(check_result, AssetCheckResult)
    ]

    if len(mat_results) == 0:
        raise DagsterPipesError("No materialization results received from external process.")

    if len(mat_results) > 1:
        raise DagsterPipesError(
            "Multiple materialize results returned with asset keys"
            f" {sorted([check.not_none(mr.asset_key).to_user_string() for mr in mat_results])}."
            " If you are materializing multiple assets in a pipes invocation, use"
            " get_results() instead.",
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


def _check_result_from_pipes_results(
    all_results: Sequence[PipesExecutionResult],
) -> AssetCheckResult:
    mat_results: List[MaterializeResult] = [
        mat_result for mat_result in all_results if isinstance(mat_result, MaterializeResult)
    ]
    check_results: List[AssetCheckResult] = [
        check_result for check_result in all_results if isinstance(check_result, AssetCheckResult)
    ]

    # return the single asset check result if thats what we got
    if len(mat_results) == 0 and len(check_results) == 1:
        return next(iter(check_results))

    # otherwise error
    raise DagsterPipesError(
        f"Did not find singular AssetCheckResult, got {len(mat_results)} MaterializeResults and"
        f" {len(check_results)} AssetCheckResults. Correct the reported results or use"
        " get_results() instead.",
    )
