from contextlib import contextmanager
from dataclasses import dataclass
from queue import Queue
from typing import Any, Dict, Iterator, Mapping, Optional, Set, Union

from dagster_pipes import (
    DAGSTER_PIPES_BOOTSTRAP_PARAM_NAMES,
    IS_DAGSTER_PIPES_PROCESS,
    PIPES_METADATA_TYPE_INFER,
    PipesContextData,
    PipesDataProvenance,
    PipesExtras,
    PipesMessage,
    PipesMetadataType,
    PipesMetadataValue,
    PipesParams,
    PipesTimeWindow,
    encode_env_var,
)
from typing_extensions import TypeAlias

import dagster._check as check
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
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.invocation import BoundOpExecutionContext
from dagster._core.pipes.client import PipesMessageReader

PipesExecutionResult: TypeAlias = Union[MaterializeResult, AssetCheckResult]


@experimental
class PipesMessageHandler:
    """Class to process :py:obj:`PipesMessage` objects received from a pipes process.

    Args:
        context (OpExecutionContext): The context for the executing op/asset.
    """

    def __init__(self, context: OpExecutionContext) -> None:
        self._context = context
        # Queue is thread-safe
        self._result_queue: Queue[PipesExecutionResult] = Queue()
        # Only read by the main thread after all messages are handled, so no need for a lock
        self._unmaterialized_assets: Set[AssetKey] = set(context.selected_asset_keys)

    @contextmanager
    def handle_messages(self, message_reader: PipesMessageReader) -> Iterator[PipesParams]:
        with message_reader.read_messages(self) as params:
            yield params
        for key in self._unmaterialized_assets:
            self._result_queue.put(MaterializeResult(asset_key=key))

    def clear_result_queue(self) -> Iterator[PipesExecutionResult]:
        while not self._result_queue.empty():
            yield self._result_queue.get()

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
        if message["method"] == "report_asset_materialization":
            self._handle_report_asset_materialization(**message["params"])  # type: ignore
        elif message["method"] == "report_asset_check":
            self._handle_report_asset_check(**message["params"])  # type: ignore
        elif message["method"] == "log":
            self._handle_log(**message["params"])  # type: ignore

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
        self._unmaterialized_assets.remove(resolved_asset_key)

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
            DAGSTER_PIPES_BOOTSTRAP_PARAM_NAMES[IS_DAGSTER_PIPES_PROCESS]: True,
            DAGSTER_PIPES_BOOTSTRAP_PARAM_NAMES["context"]: self.context_injector_params,
            DAGSTER_PIPES_BOOTSTRAP_PARAM_NAMES["messages"]: self.message_reader_params,
        }

    @public
    def get_results(self) -> Iterator[PipesExecutionResult]:
        """Iterator over buffered :py:class:`PipesExecutionResult` objects received from the
        external process.

        When this is called it clears the results buffer.

        Yields:
            ExtResult: Result reported by external process.
        """
        yield from self.message_handler.clear_result_queue()


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
        job_name=None if isinstance(context, BoundOpExecutionContext) else context.job_name,
        retry_number=0 if isinstance(context, BoundOpExecutionContext) else context.retry_number,
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
