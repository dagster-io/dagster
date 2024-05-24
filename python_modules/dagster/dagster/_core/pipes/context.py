from contextlib import contextmanager
from dataclasses import dataclass
from queue import Queue
from typing import TYPE_CHECKING, Any, Dict, Iterator, Mapping, Optional, Sequence, Union, cast

from dagster_pipes import (
    DAGSTER_PIPES_CONTEXT_ENV_VAR,
    DAGSTER_PIPES_MESSAGES_ENV_VAR,
    PIPES_METADATA_TYPE_INFER,
    Method,
    PipesContextData,
    PipesDataProvenance,
    PipesException,
    PipesExtras,
    PipesMessage,
    PipesMetadataType,
    PipesMetadataValue,
    PipesOpenedData,
    PipesParams,
    PipesTimeWindow,
    encode_env_var,
)
from typing_extensions import TypeAlias

import dagster._check as check
from dagster import DagsterEvent
from dagster._annotations import experimental, public
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.data_version import DataProvenance, DataVersion
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataValue, normalize_metadata_value
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.result import MaterializeResult
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    has_one_dimension_time_window_partitioning,
)
from dagster._core.errors import DagsterPipesExecutionError
from dagster._core.events import EngineEventData
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.invocation import BaseDirectExecutionContext
from dagster._utils.error import (
    ExceptionInfo,
    SerializableErrorInfo,
    serializable_error_info_from_exc_info,
)

if TYPE_CHECKING:
    from dagster._core.pipes.client import PipesMessageReader


PipesExecutionResult: TypeAlias = Union[MaterializeResult, AssetCheckResult]


@experimental
class PipesMessageHandler:
    """Class to process :py:obj:`PipesMessage` objects received from a pipes process.

    Args:
        context (OpExecutionContext): The context for the executing op/asset.
        message_reader (PipesMessageReader): The message reader used to read messages from the
            external process.
    """

    # In the future it may make sense to merge PipesMessageReader and PipesMessageHandler, or
    # otherwise adjust their relationship. The current interaction between the two is a bit awkward,
    # but it would also be awkward to have a monolith that users extend.
    def __init__(self, context: OpExecutionContext, message_reader: "PipesMessageReader") -> None:
        self._context = context
        self._message_reader = message_reader
        # Queue is thread-safe
        self._result_queue: Queue[PipesExecutionResult] = Queue()
        self._extra_msg_queue: Queue[Any] = Queue()
        # Only read by the main thread after all messages are handled, so no need for a lock
        self._received_opened_msg = False
        self._received_closed_msg = False
        self._opened_payload: Optional[PipesOpenedData] = None

    @contextmanager
    def handle_messages(self) -> Iterator[PipesParams]:
        with self._message_reader.read_messages(self) as params:
            yield params

    def get_reported_results(self) -> Sequence[PipesExecutionResult]:
        return tuple(self._result_queue.queue)

    def get_custom_messages(self) -> Sequence[Any]:
        return tuple(self._extra_msg_queue.queue)

    @property
    def received_opened_message(self) -> bool:
        return self._received_opened_msg

    @property
    def received_closed_message(self) -> bool:
        return self._received_closed_msg

    def _resolve_metadata(
        self, metadata: Mapping[str, PipesMetadataValue]
    ) -> Mapping[str, MetadataValue]:
        return {
            k: self._resolve_metadata_value(v["raw_value"], v["type"]) for k, v in metadata.items()
        }

    def _resolve_metadata_value(
        self, value: Any, metadata_type: PipesMetadataType
    ) -> MetadataValue:
        if metadata_type == PIPES_METADATA_TYPE_INFER:
            return normalize_metadata_value(value)
        elif metadata_type == "text":
            return MetadataValue.text(value)
        elif metadata_type == "url":
            return MetadataValue.url(value)
        elif metadata_type == "path":
            return MetadataValue.path(value)
        elif metadata_type == "notebook":
            return MetadataValue.notebook(value)
        elif metadata_type == "json":
            return MetadataValue.json(value)
        elif metadata_type == "md":
            return MetadataValue.md(value)
        elif metadata_type == "float":
            return MetadataValue.float(value)
        elif metadata_type == "int":
            return MetadataValue.int(value)
        elif metadata_type == "bool":
            return MetadataValue.bool(value)
        elif metadata_type == "dagster_run":
            return MetadataValue.dagster_run(value)
        elif metadata_type == "asset":
            return MetadataValue.asset(AssetKey.from_user_string(value))
        elif metadata_type == "table":
            return MetadataValue.table(value)
        elif metadata_type == "null":
            return MetadataValue.null()
        else:
            check.failed(f"Unexpected metadata type {metadata_type}")

    # Type ignores because we currently validate in individual handlers
    def handle_message(self, message: PipesMessage) -> None:
        if self._received_closed_msg:
            self._context.log.warn(f"[pipes] unexpected message received after closed: `{message}`")

        method = cast(Method, message["method"])
        if method == "opened":
            self._handle_opened(message["params"])  # type: ignore
        elif method == "closed":
            self._handle_closed(message["params"])
        elif method == "report_asset_materialization":
            self._handle_report_asset_materialization(**message["params"])  # type: ignore
        elif method == "report_asset_check":
            self._handle_report_asset_check(**message["params"])  # type: ignore
        elif method == "log":
            self._handle_log(**message["params"])  # type: ignore
        elif method == "report_custom_message":
            self._handle_extra_message(**message["params"])  # type: ignore
        else:
            raise DagsterPipesExecutionError(f"Unknown message method: {message['method']}")

    def _handle_opened(self, opened_payload: PipesOpenedData) -> None:
        self._received_opened_msg = True
        self._context.log.info("[pipes] external process successfully opened dagster pipes.")
        self._message_reader.on_opened(opened_payload)

    def _handle_closed(self, params: Optional[Mapping[str, Any]]) -> None:
        self._received_closed_msg = True
        if params and "exception" in params:
            err_info = _ser_err_from_pipes_exc(params["exception"])
            # report as an engine event to provide structured exception data
            DagsterEvent.engine_event(
                self._context.get_step_execution_context(),
                "[pipes] external process pipes closed with exception",
                EngineEventData(error=err_info),
            )

    def _handle_report_asset_materialization(
        self,
        asset_key: str,
        metadata: Optional[Mapping[str, PipesMetadataValue]],
        data_version: Optional[str],
    ) -> None:
        check.str_param(asset_key, "asset_key")
        check.opt_str_param(data_version, "data_version")
        metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        resolved_asset_key = AssetKey.from_user_string(asset_key)
        resolved_metadata = self._resolve_metadata(metadata)
        resolved_data_version = None if data_version is None else DataVersion(data_version)
        result = MaterializeResult(
            asset_key=resolved_asset_key,
            metadata=resolved_metadata,
            data_version=resolved_data_version,
        )
        self._result_queue.put(result)

    def _handle_report_asset_check(
        self,
        asset_key: str,
        check_name: str,
        passed: bool,
        severity: str,
        metadata: Mapping[str, PipesMetadataValue],
    ) -> None:
        check.str_param(asset_key, "asset_key")
        check.str_param(check_name, "check_name")
        check.bool_param(passed, "passed")
        check.literal_param(severity, "severity", [x.value for x in AssetCheckSeverity])
        metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        resolved_asset_key = AssetKey.from_user_string(asset_key)
        resolved_metadata = self._resolve_metadata(metadata)
        resolved_severity = AssetCheckSeverity(severity)
        result = AssetCheckResult(
            asset_key=resolved_asset_key,
            check_name=check_name,
            passed=passed,
            severity=resolved_severity,
            metadata=resolved_metadata,
        )
        self._result_queue.put(result)

    def _handle_log(self, message: str, level: str = "info") -> None:
        check.str_param(message, "message")
        self._context.log.log(level, message)

    def _handle_extra_message(self, payload: Any):
        self._extra_msg_queue.put(payload)

    def report_pipes_framework_exception(self, origin: str, exc_info: ExceptionInfo):
        # use an engine event to provide structured exception, this gives us an event with
        # * the context of where the exception happened ([pipes]...)
        # * the exception class, message, and stack trace as well as any chained exception
        DagsterEvent.engine_event(
            self._context.get_step_execution_context(),
            f"[pipes] framework exception occurred in {origin}",
            EngineEventData(
                error=serializable_error_info_from_exc_info(exc_info),
            ),
        )


@experimental
@dataclass
class PipesSession:
    """Object representing a pipes session.

    A pipes session is defined by a pair of :py:class:`PipesContextInjector` and
    :py:class:`PipesMessageReader` objects. At the opening of the session, the context injector
    writes context data to an externally accessible location, and the message reader starts
    monitoring an externally accessible location. These locations are encoded in parameters stored
    on a `PipesSession` object.

    During the session, an external process should be started and the parameters injected into its
    environment. The typical way to do this is to call :py:meth:`PipesSession.get_bootstrap_env_vars`
    and pass the result as environment variables.

    During execution, results (e.g. asset materializations) are reported by the external process and
    buffered on the `PipesSession` object. The buffer can periodically be cleared and yielded to
    Dagster machinery by calling `yield from PipesSession.get_results()`.

    When the external process exits, the session can be closed. Closing consists of handling any
    unprocessed messages written by the external process and cleaning up any resources used for
    context injection and message reading.

    Args:
        context_data (PipesContextData): The context for the executing op/asset.
        message_handler (PipesMessageHandler): The message handler to use for processing messages
        context_injector_params (PipesParams): Parameters yielded by the context injector,
            indicating the location from which the external process should load context data.
        message_reader_params (PipesParams): Parameters yielded by the message reader, indicating
            the location to which the external process should write messages.
    """

    context_data: PipesContextData
    message_handler: PipesMessageHandler
    context_injector_params: PipesParams
    message_reader_params: PipesParams
    context: OpExecutionContext

    @public
    def get_bootstrap_env_vars(self) -> Dict[str, str]:
        """Encode context injector and message reader params as environment variables.

        Passing environment variables is the typical way to expose the pipes I/O parameters
        to a pipes process.

        Returns:
            Mapping[str, str]: Environment variables to pass to the external process. The values are
            serialized as json, compressed with gzip, and then base-64-encoded.
        """
        return {
            param_name: encode_env_var(param_value)
            for param_name, param_value in self.get_bootstrap_params().items()
        }

    @public
    def get_bootstrap_params(self) -> Dict[str, Any]:
        """Get the params necessary to bootstrap a launched pipes process. These parameters are typically
        are as environment variable. See `get_bootstrap_env_vars`. It is the context injector's
        responsibility to decide how to pass these parameters to the external environment.

        Returns:
            Mapping[str, str]: Parameters to pass to the external process and their corresponding
            values that must be passed by the context injector.
        """
        return {
            DAGSTER_PIPES_CONTEXT_ENV_VAR: self.context_injector_params,
            DAGSTER_PIPES_MESSAGES_ENV_VAR: self.message_reader_params,
        }

    @public
    def get_results(
        self,
        *,
        implicit_materializations: bool = True,
    ) -> Sequence[PipesExecutionResult]:
        """:py:class:`PipesExecutionResult` objects reported from the external process.

        Args:
            implicit_materializations (bool): Create MaterializeResults for expected assets
                even was nothing is reported from the external process.

        Returns:
            Sequence[PipesExecutionResult]: Result reported by external process.
        """
        reported = self.message_handler.get_reported_results()
        if not implicit_materializations:
            return reported

        reported_keys = set(
            result.asset_key for result in reported if isinstance(result, MaterializeResult)
        )
        implicit = (
            MaterializeResult(asset_key=key)
            for key in self.context.selected_asset_keys
            if key not in reported_keys
        )

        return (
            *reported,
            *implicit,
        )

    @public
    def get_reported_results(self) -> Sequence[PipesExecutionResult]:
        """:py:class:`PipesExecutionResult` objects only explicitly received from the external process.

        Returns:
            Sequence[PipesExecutionResult]: Result reported by external process.
        """
        return self.message_handler.get_reported_results()

    @public
    def get_custom_messages(self) -> Sequence[Any]:
        """Get the sequence of deserialized JSON data that was reported from the external process using
        `report_custom_message`.

        Returns: Sequence[Any]
        """
        return self.message_handler.get_custom_messages()


def build_external_execution_context_data(
    context: OpExecutionContext,
    extras: Optional[PipesExtras],
) -> "PipesContextData":
    asset_keys = (
        [_convert_asset_key(key) for key in sorted(context.selected_asset_keys)]
        if context.has_assets_def
        else None
    )
    code_version_by_asset_key = (
        {
            _convert_asset_key(key): context.assets_def.code_versions_by_key[key]
            for key in context.selected_asset_keys
        }
        if context.has_assets_def
        else None
    )
    provenance_by_asset_key = (
        {
            _convert_asset_key(key): _convert_data_provenance(context.get_asset_provenance(key))
            for key in context.selected_asset_keys
        }
        if context.has_assets_def
        else None
    )
    partition_key = context.partition_key if context.has_partition_key else None
    partition_key_range = context.partition_key_range if context.has_partition_key else None
    partition_time_window = (
        context.partition_time_window
        if context.has_partition_key
        and has_one_dimension_time_window_partitioning(
            context.get_step_execution_context().partitions_def
        )
        else None
    )
    return PipesContextData(
        asset_keys=asset_keys,
        code_version_by_asset_key=code_version_by_asset_key,
        provenance_by_asset_key=provenance_by_asset_key,
        partition_key=partition_key,
        partition_key_range=(
            _convert_partition_key_range(partition_key_range) if partition_key_range else None
        ),
        partition_time_window=(
            _convert_time_window(partition_time_window) if partition_time_window else None
        ),
        run_id=context.run_id,
        job_name=None if isinstance(context, BaseDirectExecutionContext) else context.job_name,
        retry_number=0 if isinstance(context, BaseDirectExecutionContext) else context.retry_number,
        extras=extras or {},
    )


def _convert_asset_key(asset_key: AssetKey) -> str:
    return asset_key.to_user_string()


def _convert_data_provenance(
    provenance: Optional[DataProvenance],
) -> Optional["PipesDataProvenance"]:
    return (
        None
        if provenance is None
        else PipesDataProvenance(
            code_version=provenance.code_version,
            input_data_versions={
                _convert_asset_key(k): v.value for k, v in provenance.input_data_versions.items()
            },
            is_user_provided=provenance.is_user_provided,
        )
    )


def _convert_time_window(
    time_window: TimeWindow,
) -> "PipesTimeWindow":
    return PipesTimeWindow(
        start=time_window.start.isoformat(),
        end=time_window.end.isoformat(),
    )


def _convert_partition_key_range(
    partition_key_range: PartitionKeyRange,
) -> "PipesTimeWindow":
    return PipesTimeWindow(
        start=partition_key_range.start,
        end=partition_key_range.end,
    )


def _ser_err_from_pipes_exc(exc: PipesException):
    return SerializableErrorInfo(
        message=exc["message"],
        stack=exc["stack"],
        cls_name=exc["name"],
        cause=_ser_err_from_pipes_exc(exc["cause"]) if exc["cause"] else None,
        context=_ser_err_from_pipes_exc(exc["context"]) if exc["context"] else None,
    )
