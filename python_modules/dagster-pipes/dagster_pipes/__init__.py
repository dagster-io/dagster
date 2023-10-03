import atexit
import base64
import datetime
import json
import logging
import os
import sys
import time
import warnings
import zlib
from abc import ABC, abstractmethod
from contextlib import ExitStack, contextmanager
from io import StringIO
from threading import Event, Lock, Thread
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    TextIO,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    get_args,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

# ########################
# ##### PROTOCOL
# ########################

# This represents the version of the protocol, rather than the version of the package. It must be
# manually updated whenever there are changes to the protocol.
PIPES_PROTOCOL_VERSION = "0.1"

PipesExtras = Mapping[str, Any]
PipesParams = Mapping[str, Any]


_ENV_KEY_PREFIX = "DAGSTER_PIPES_"


def _param_name_to_env_key(key: str) -> str:
    return f"{_ENV_KEY_PREFIX}{key.upper()}"


def _make_message(method: str, params: Optional[Mapping[str, Any]]) -> "PipesMessage":
    return {
        PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
        "method": method,
        "params": params,
    }


# ##### PARAMETERS

IS_DAGSTER_PIPES_PROCESS = "IS_DAGSTER_PIPED_PROCESS"

DAGSTER_PIPES_BOOTSTRAP_PARAM_NAMES = {
    k: _param_name_to_env_key(k) for k in (IS_DAGSTER_PIPES_PROCESS, "context", "messages")
}


# ##### MESSAGE

# Can't use a constant for TypedDict key so this value is repeated in `ExtMessage` defn.
PIPES_PROTOCOL_VERSION_FIELD = "__dagster_pipes_version"


class PipesMessage(TypedDict):
    """A message sent from the orchestration process to the external process."""

    __dagster_pipes_version: str
    method: str
    params: Optional[Mapping[str, Any]]


###### PIPES CONTEXT


class PipesContextData(TypedDict):
    """The serializable data passed from the orchestration process to the external process. This gets
    wrapped in a :py:class:`PipesContext`.
    """

    asset_keys: Optional[Sequence[str]]
    code_version_by_asset_key: Optional[Mapping[str, Optional[str]]]
    provenance_by_asset_key: Optional[Mapping[str, Optional["PipesDataProvenance"]]]
    partition_key: Optional[str]
    partition_key_range: Optional["PipesPartitionKeyRange"]
    partition_time_window: Optional["PipesTimeWindow"]
    run_id: str
    job_name: Optional[str]
    retry_number: int
    extras: Mapping[str, Any]


class PipesPartitionKeyRange(TypedDict):
    """A range of partition keys."""

    start: str
    end: str


class PipesTimeWindow(TypedDict):
    """A span of time delimited by a start and end timestamp. This is defined for time-based partitioning schemes."""

    start: str  # timestamp
    end: str  # timestamp


class PipesDataProvenance(TypedDict):
    """Provenance information for an asset."""

    code_version: str
    input_data_versions: Mapping[str, str]
    is_user_provided: bool


PipesAssetCheckSeverity = Literal["WARN", "ERROR"]

PipesMetadataRawValue = Union[int, float, str, Mapping[str, Any], Sequence[Any], bool, None]


class PipesMetadataValue(TypedDict):
    type: "PipesMetadataType"
    raw_value: PipesMetadataRawValue


# Infer the type from the raw value on the orchestration end
PIPES_METADATA_TYPE_INFER = "__infer__"

PipesMetadataType = Literal[
    "__infer__",
    "text",
    "url",
    "path",
    "notebook",
    "json",
    "md",
    "float",
    "int",
    "bool",
    "dagster_run",
    "asset",
    "null",
]

# ########################
# ##### UTIL
# ########################

_T = TypeVar("_T")


class DagsterPipesError(Exception):
    pass


class DagsterPipesWarning(Warning):
    pass


def _assert_not_none(value: Optional[_T], desc: Optional[str] = None) -> _T:
    if value is None:
        raise DagsterPipesError(f"Missing required property: {desc}")
    return value


def _assert_defined_asset_property(value: Optional[_T], key: str) -> _T:
    return _assert_not_none(value, f"`{key}` is undefined. Current step does not target an asset.")


# This should only be called under the precondition that the current step targets assets.
def _assert_single_asset(data: PipesContextData, key: str) -> None:
    asset_keys = data["asset_keys"]
    assert asset_keys is not None
    if len(asset_keys) != 1:
        raise DagsterPipesError(f"`{key}` is undefined. Current step targets multiple assets.")


def _resolve_optionally_passed_asset_key(
    data: PipesContextData,
    asset_key: Optional[str],
    method: str,
) -> str:
    asset_keys = _assert_defined_asset_property(data["asset_keys"], method)
    asset_key = _assert_opt_param_type(asset_key, str, method, "asset_key")
    if asset_key and asset_key not in asset_keys:
        raise DagsterPipesError(
            f"Invalid asset key. Expected one of `{asset_keys}`, got `{asset_key}`."
        )
    if not asset_key:
        if len(asset_keys) != 1:
            raise DagsterPipesError(
                f"Calling `{method}` without passing an asset key is undefined. Current step"
                " targets multiple assets."
            )
        asset_key = asset_keys[0]
    return asset_key


def _assert_defined_partition_property(value: Optional[_T], key: str) -> _T:
    return _assert_not_none(
        value, f"`{key}` is undefined. Current step does not target any partitions."
    )


# This should only be called under the precondition that the current steps targets assets.
def _assert_single_partition(data: PipesContextData, key: str) -> None:
    partition_key_range = data["partition_key_range"]
    assert partition_key_range is not None
    if partition_key_range["start"] != partition_key_range["end"]:
        raise DagsterPipesError(f"`{key}` is undefined. Current step targets multiple partitions.")


def _assert_defined_extra(extras: PipesExtras, key: str) -> Any:
    if key not in extras:
        raise DagsterPipesError(f"Extra `{key}` is undefined. Extras must be provided by user.")
    return extras[key]


def _assert_param_type(value: _T, expected_type: Any, method: str, param: str) -> _T:
    if not isinstance(value, expected_type):
        raise DagsterPipesError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected `{expected_type}`, got"
            f" `{type(value)}`."
        )
    return value


def _assert_opt_param_type(value: _T, expected_type: Any, method: str, param: str) -> _T:
    if not (isinstance(value, expected_type) or value is None):
        raise DagsterPipesError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected"
            f" `Optional[{expected_type}]`, got `{type(value)}`."
        )
    return value


def _assert_env_param_type(
    env_params: PipesParams, key: str, expected_type: Type[_T], cls: Type
) -> _T:
    value = env_params.get(key)
    if not isinstance(value, expected_type):
        raise DagsterPipesError(
            f"Invalid type for parameter `{key}` passed from orchestration side to"
            f" `{cls.__name__}`. Expected `{expected_type}`, got `{type(value)}`."
        )
    return value


def _assert_opt_env_param_type(
    env_params: PipesParams, key: str, expected_type: Type[_T], cls: Type
) -> Optional[_T]:
    value = env_params.get(key)
    if value is not None and not isinstance(value, expected_type):
        raise DagsterPipesError(
            f"Invalid type for parameter `{key}` passed from orchestration side to"
            f" `{cls.__name__}`. Expected `Optional[{expected_type}]`, got `{type(value)}`."
        )
    return value


def _assert_param_value(value: _T, expected_values: Iterable[_T], method: str, param: str) -> _T:
    if value not in expected_values:
        raise DagsterPipesError(
            f"Invalid value for parameter `{param}` of `{method}`. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def _assert_opt_param_value(
    value: _T, expected_values: Sequence[_T], method: str, param: str
) -> _T:
    if value is not None and value not in expected_values:
        raise DagsterPipesError(
            f"Invalid value for parameter `{param}` of `{method}`. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def _json_serialize_param(value: Any, method: str, param: str) -> str:
    try:
        serialized = json.dumps(value)
    except (TypeError, OverflowError):
        raise DagsterPipesError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected a JSON-serializable"
            f" type, got `{type(value)}`."
        )
    return serialized


_METADATA_VALUE_KEYS = frozenset(PipesMetadataValue.__annotations__.keys())
_METADATA_TYPES = frozenset(get_args(PipesMetadataType))


def _normalize_param_metadata(
    metadata: Mapping[str, Union[PipesMetadataRawValue, PipesMetadataValue]],
    method: str,
    param: str,
) -> Mapping[str, Union[PipesMetadataRawValue, PipesMetadataValue]]:
    _assert_param_type(metadata, dict, method, param)
    new_metadata: Dict[str, PipesMetadataValue] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise DagsterPipesError(
                f"Invalid type for parameter `{param}` of `{method}`. Expected a dict with string"
                f" keys, got a key `{key}` of type `{type(key)}`."
            )
        elif isinstance(value, dict):
            if not {*value.keys()} == _METADATA_VALUE_KEYS:
                raise DagsterPipesError(
                    f"Invalid type for parameter `{param}` of `{method}`. Expected a dict with"
                    " string keys and values that are either raw metadata values or dictionaries"
                    f" with schema `{{raw_value: ..., type: ...}}`. Got a value `{value}`."
                )
            _assert_param_value(value["type"], _METADATA_TYPES, method, f"{param}.{key}.type")
            new_metadata[key] = cast(PipesMetadataValue, value)
        else:
            new_metadata[key] = {"raw_value": value, "type": PIPES_METADATA_TYPE_INFER}
    return new_metadata


def _param_from_env_var(key: str) -> Any:
    raw_value = os.environ.get(_param_name_to_env_var(key))
    return decode_env_var(raw_value) if raw_value is not None else None


def encode_env_var(value: Any) -> str:
    """Encode value by serializing to JSON, compressing with zlib, and finally encoding with base64.
    `base64_encode(compress(to_json(value)))` in function notation.

    Args:
        value (Any): The value to encode. Must be JSON-serializable.

    Returns:
        str: The encoded value.
    """
    serialized = _json_serialize_param(value, "encode_env_var", "value")
    compressed = zlib.compress(serialized.encode("utf-8"))
    encoded = base64.b64encode(compressed)
    return encoded.decode("utf-8")  # as string


def decode_env_var(value: str) -> Any:
    """Decode a value by decoding from base64, decompressing with zlib, and finally deserializing from
    JSON. `from_json(decompress(base64_decode(value)))` in function notation.

    Args:
        value (Any): The value to decode.

    Returns:
        Any: The decoded value.
    """
    decoded = base64.b64decode(value)
    decompressed = zlib.decompress(decoded)
    return json.loads(decompressed.decode("utf-8"))


def _param_name_to_env_var(param_name: str) -> str:
    return f"{_ENV_KEY_PREFIX}{param_name.upper()}"


def _env_var_to_param_name(env_var: str) -> str:
    return env_var[len(_ENV_KEY_PREFIX) :].lower()


def is_dagster_pipes_process() -> bool:
    return _param_from_env_var(IS_DAGSTER_PIPES_PROCESS)


def _emit_orchestration_inactive_warning() -> None:
    warnings.warn(
        "This process was not launched by a Dagster orchestration process. All calls to the"
        " `dagster-pipes` context or attempts to initialize `dagster-pipes` abstractions"
        " are no-ops.",
        category=DagsterPipesWarning,
    )


def _get_mock() -> "MagicMock":
    from unittest.mock import MagicMock

    return MagicMock()


class _PipesLogger(logging.Logger):
    def __init__(self, context: "PipesContext") -> None:
        super().__init__(name="dagster-pipes")
        self.addHandler(_PipesLoggerHandler(context))


class _PipesLoggerHandler(logging.Handler):
    def __init__(self, context: "PipesContext") -> None:
        super().__init__()
        self._context = context

    def emit(self, record: logging.LogRecord) -> None:
        self._context._write_message(  # noqa: SLF001
            "log", {"message": record.getMessage(), "level": record.levelname}
        )


# ########################
# ##### IO - BASE
# ########################


class PipesContextLoader(ABC):
    @abstractmethod
    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        """A `@contextmanager` that loads context data injected by the orchestration process.

        This method should read and yield the context data from the location specified by the passed in
        `PipesParams`.

        Args:
            params (PipesParams): The params provided by the context injector in the orchestration
                process.

        Yields:
            PipesContextData: The context data.
        """


T_MessageChannel = TypeVar("T_MessageChannel", bound="PipesMessageWriterChannel")


class PipesMessageWriter(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    @contextmanager
    def open(self, params: PipesParams) -> Iterator[T_MessageChannel]:
        """A `@contextmanager` that initializes a channel for writing messages back to Dagster.

        This method should takes the params passed by the orchestration-side
        :py:class:`PipesMessageReader` and use them to construct and yield a
        :py:class:`PipesMessageWriterChannel`.

        Args:
            params (PipesParams): The params provided by the message reader in the orchestration
                process.

        Yields:
            PipesMessageWriterChannel: Channel for writing messagse back to Dagster.
        """


class PipesMessageWriterChannel(ABC, Generic[T_MessageChannel]):
    """Object that writes messages back to the Dagster orchestration process."""

    @abstractmethod
    def write_message(self, message: PipesMessage) -> None:
        """Write a message to the orchestration process.

        Args:
            message (PipesMessage): The message to write.
        """


class PipesParamsLoader(ABC):
    """Object that loads params passed from the orchestration process by the context injector and
    message reader. These params are used to respectively bootstrap the
    :py:class:`PipesContextLoader` and :py:class:`PipesMessageWriter`.
    """

    @abstractmethod
    def load_context_params(self) -> PipesParams:
        """PipesParams: Load params passed by the orchestration-side context injector."""

    @abstractmethod
    def load_messages_params(self) -> PipesParams:
        """PipesParams: Load params passed by the orchestration-side message reader."""


T_BlobStoreMessageWriterChannel = TypeVar(
    "T_BlobStoreMessageWriterChannel", bound="PipesBlobStoreMessageWriterChannel"
)


class PipesBlobStoreMessageWriter(PipesMessageWriter[T_BlobStoreMessageWriterChannel]):
    """Message writer channel that periodically uploads message chunks to some blob store endpoint."""

    def __init__(self, *, interval: float = 10):
        self.interval = interval

    @contextmanager
    def open(self, params: PipesParams) -> Iterator[T_BlobStoreMessageWriterChannel]:
        """Construct and yield a :py:class:`PipesBlobStoreMessageWriterChannel`.

        Args:
            params (PipesParams): The params provided by the message reader in the orchestration
                process.

        Yields:
            PipesBlobStoreMessageWriterChannel: Channel that periodically uploads message chunks to
            a blob store.
        """
        channel = self.make_channel(params)
        with channel.buffered_upload_loop():
            yield channel

    @abstractmethod
    def make_channel(self, params: PipesParams) -> T_BlobStoreMessageWriterChannel: ...


class PipesBlobStoreMessageWriterChannel(PipesMessageWriterChannel):
    """Message writer channel that periodically uploads message chunks to some blob store endpoint."""

    def __init__(self, *, interval: float = 10):
        self._interval = interval
        self._lock = Lock()
        self._buffer = []
        self._counter = 1

    def write_message(self, message: PipesMessage) -> None:
        with self._lock:
            self._buffer.append(message)

    def flush_messages(self) -> Sequence[PipesMessage]:
        with self._lock:
            messages = list(self._buffer)
            self._buffer.clear()
            return messages

    @abstractmethod
    def upload_messages_chunk(self, payload: StringIO, index: int) -> None: ...

    @contextmanager
    def buffered_upload_loop(self) -> Iterator[None]:
        thread = None
        is_task_complete = Event()
        try:
            thread = Thread(target=self._upload_loop, args=(is_task_complete,), daemon=True)
            thread.start()
            yield
        finally:
            is_task_complete.set()
            if thread:
                thread.join(timeout=60)

    def _upload_loop(self, is_task_complete: Event) -> None:
        start_or_last_upload = datetime.datetime.now()
        while True:
            num_pending = len(self._buffer)
            now = datetime.datetime.now()
            if num_pending == 0 and is_task_complete.is_set():
                break
            elif is_task_complete.is_set() or (now - start_or_last_upload).seconds > self._interval:
                payload = "\n".join([json.dumps(message) for message in self.flush_messages()])
                self.upload_messages_chunk(StringIO(payload), self._counter)
                start_or_last_upload = now
                self._counter += 1
            time.sleep(1)


class PipesBufferedFilesystemMessageWriterChannel(PipesBlobStoreMessageWriterChannel):
    """Message writer channel that periodically writes message chunks to an endpoint mounted on the filesystem.

    Args:
        interval (float): interval in seconds between chunk uploads
    """

    def __init__(self, path: str, *, interval: float = 10):
        super().__init__(interval=interval)
        self._path = path

    def upload_messages_chunk(self, payload: IO, index: int) -> None:
        message_path = os.path.join(self._path, f"{index}.json")
        with open(message_path, "w") as f:
            f.write(payload.read())


# ########################
# ##### IO - DEFAULT
# ########################


class PipesDefaultContextLoader(PipesContextLoader):
    """Context loader that loads context data from either a file or directly from the provided params.

    The location of the context data is configured by the params received by the loader. If the params
    include a key `path`, then the context data will be loaded from a file at the specified path. If
    the params instead include a key `data`, then the corresponding value should be a dict
    representing the context data.
    """

    FILE_PATH_KEY = "path"
    DIRECT_KEY = "data"

    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        if self.FILE_PATH_KEY in params:
            path = _assert_env_param_type(params, self.FILE_PATH_KEY, str, self.__class__)
            with open(path, "r") as f:
                data = json.load(f)
                yield data
        elif self.DIRECT_KEY in params:
            data = _assert_env_param_type(params, self.DIRECT_KEY, dict, self.__class__)
            yield cast(PipesContextData, data)
        else:
            raise DagsterPipesError(
                f'Invalid params for {self.__class__.__name__}, expected key "{self.FILE_PATH_KEY}"'
                f' or "{self.DIRECT_KEY}", received {params}',
            )


class PipesDefaultMessageWriter(PipesMessageWriter):
    """Message writer that writes messages to either a file or the stdout or stderr stream.

    The write location is configured by the params received by the writer. If the params include a
    key `path`, then messages will be written to a file at the specified path. If the params instead
    include a key `stdio`, then messages then the corresponding value must specify either `stderr`
    or `stdout`, and messages will be written to the selected stream.
    """

    FILE_PATH_KEY = "path"
    STDIO_KEY = "stdio"
    STDERR = "stderr"
    STDOUT = "stdout"

    @contextmanager
    def open(self, params: PipesParams) -> Iterator[PipesMessageWriterChannel]:
        if self.FILE_PATH_KEY in params:
            path = _assert_env_param_type(params, self.FILE_PATH_KEY, str, self.__class__)
            yield PipesFileMessageWriterChannel(path)
        elif self.STDIO_KEY in params:
            stream = _assert_env_param_type(params, self.STDIO_KEY, str, self.__class__)
            if stream == self.STDERR:
                yield PipesStreamMessageWriterChannel(sys.stderr)
            elif stream == self.STDOUT:
                yield PipesStreamMessageWriterChannel(sys.stdout)
            else:
                raise DagsterPipesError(
                    f'Invalid value for key "std", expected "{self.STDERR}" or "{self.STDOUT}" but'
                    f" received {stream}"
                )
        else:
            raise DagsterPipesError(
                f'Invalid params for {self.__class__.__name__}, expected key "path" or "std",'
                f" received {params}"
            )


class PipesFileMessageWriterChannel(PipesMessageWriterChannel):
    """Message writer channel that writes one message per line to a file."""

    def __init__(self, path: str):
        self._path = path

    def write_message(self, message: PipesMessage) -> None:
        with open(self._path, "a") as f:
            f.write(json.dumps(message) + "\n")


class PipesStreamMessageWriterChannel(PipesMessageWriterChannel):
    """Message writer channel that writes one message per line to a `TextIO` stream."""

    def __init__(self, stream: TextIO):
        self._stream = stream

    def write_message(self, message: PipesMessage) -> None:
        self._stream.writelines((json.dumps(message), "\n"))


class PipesEnvVarParamsLoader(PipesParamsLoader):
    """Params loader that extracts params from environment variables."""

    def load_context_params(self) -> PipesParams:
        return _param_from_env_var("context")

    def load_messages_params(self) -> PipesParams:
        return _param_from_env_var("messages")


# ########################
# ##### IO - S3
# ########################


class PipesS3MessageWriter(PipesBlobStoreMessageWriter):
    """Message writer that writes messages by periodically writing message chunks to an S3 bucket.

    Args:
        client (Any): A boto3.client("s3") object.
        interval (float): interval in seconds between upload chunk uploads
    """

    # client is a boto3.client("s3") object
    def __init__(self, client: Any, *, interval: float = 10):
        super().__init__(interval=interval)
        # Not checking client type for now because it's a boto3.client object and we don't want to
        # depend on boto3.
        self._client = client

    def make_channel(
        self,
        params: PipesParams,
    ) -> "PipesS3MessageWriterChannel":
        bucket = _assert_env_param_type(params, "bucket", str, self.__class__)
        key_prefix = _assert_opt_env_param_type(params, "key_prefix", str, self.__class__)
        return PipesS3MessageWriterChannel(
            client=self._client,
            bucket=bucket,
            key_prefix=key_prefix,
            interval=self.interval,
        )


class PipesS3MessageWriterChannel(PipesBlobStoreMessageWriterChannel):
    """Message writer channel for writing messages by periodically writing message chunks to an S3 bucket.

    Args:
        client (Any): A boto3.client("s3") object.
        bucket (str): The name of the S3 bucket to write to.
        key_prefix (Optional[str]): An optional prefix to use for the keys of written blobs.
        interval (float): interval in seconds between upload chunk uploads
    """

    # client is a boto3.client("s3") object
    def __init__(
        self, client: Any, bucket: str, key_prefix: Optional[str], *, interval: float = 10
    ):
        super().__init__(interval=interval)
        self._client = client
        self._bucket = bucket
        self._key_prefix = key_prefix

    def upload_messages_chunk(self, payload: IO, index: int) -> None:
        key = f"{self._key_prefix}/{index}.json" if self._key_prefix else f"{index}.json"
        self._client.put_object(
            Body=payload.read(),
            Bucket=self._bucket,
            Key=key,
        )


# ########################
# ##### IO - DBFS
# ########################


class PipesDbfsContextLoader(PipesContextLoader):
    """Context loader that reads context from a JSON file on DBFS."""

    @contextmanager
    def load_context(self, params: PipesParams) -> Iterator[PipesContextData]:
        unmounted_path = _assert_env_param_type(params, "path", str, self.__class__)
        path = os.path.join("/dbfs", unmounted_path.lstrip("/"))
        with open(path, "r") as f:
            yield json.load(f)


class PipesDbfsMessageWriter(PipesBlobStoreMessageWriter):
    """Message writer that writes messages by periodically writing message chunks to a directory on DBFS."""

    def make_channel(
        self,
        params: PipesParams,
    ) -> "PipesBufferedFilesystemMessageWriterChannel":
        unmounted_path = _assert_env_param_type(params, "path", str, self.__class__)
        return PipesBufferedFilesystemMessageWriterChannel(
            path=os.path.join("/dbfs", unmounted_path.lstrip("/")),
            interval=self.interval,
        )


# ########################
# ##### CONTEXT
# ########################


def open_dagster_pipes(
    *,
    context_loader: Optional[PipesContextLoader] = None,
    message_writer: Optional[PipesMessageWriter] = None,
    params_loader: Optional[PipesParamsLoader] = None,
) -> "PipesContext":
    """Initialize the Dagster Pipes context.

    This function should be called near the entry point of a pipes process. It will load injected
    context information from Dagster and spin up the machinery for streaming messages back to
    Dagster.

    If the process was not launched by Dagster, this function will emit a warning and return a
    `MagicMock` object. This should make all operations on the context no-ops and prevent your code
    from crashing. However, it is recommended to instead check :py:func:`is_dagster_pipes_process()`
    to handle the case where the process is not launched by Dagster.

    Args:
        context_loader (Optional[PipesContextLoader]): The context loader to use. Defaults to
            :py:class:`PipesDefaultContextLoader`.
        message_writer (Optional[PipesMessageWriter]): The message writer to use. Defaults to
            :py:class:`PipesDefaultMessageWriter`.
        params_loader (Optional[PipesParamsLoader]): The params loader to use. Defaults to
            :py:class:`PipesEnvVarParamsLoader`.

    Returns:
        PipesContext: The initialized context.
    """
    if PipesContext.is_initialized():
        return PipesContext.get()

    if is_dagster_pipes_process():
        params_loader = params_loader or PipesEnvVarParamsLoader()
        context_loader = context_loader or PipesDefaultContextLoader()
        message_writer = message_writer or PipesDefaultMessageWriter()
        context = PipesContext(params_loader, context_loader, message_writer)
    else:
        _emit_orchestration_inactive_warning()
        context = _get_mock()
    PipesContext.set(context)
    return context


def init_dagster_pipes(
    *,
    context_loader: Optional[PipesContextLoader] = None,
    message_writer: Optional[PipesMessageWriter] = None,
    params_loader: Optional[PipesParamsLoader] = None,
) -> "PipesContext":
    warnings.warn(
        "`init_dagster_pipes` has been renamed to `open_dagster_pipes`. `init_dagster_pipes` will"
        " be removed in 1.5.3.",
        category=DeprecationWarning,
    )
    context = open_dagster_pipes(
        context_loader=context_loader, message_writer=message_writer, params_loader=params_loader
    )
    atexit.register(context.close)
    return context


class PipesContext:
    """The context for a Dagster Pipes process.

    This class is analogous to :py:class:`~dagster.OpExecutionContext` on the Dagster side of the Pipes
    connection. It provides access to information such as the asset key(s) and partition key(s) in
    scope for the current step. It also provides methods for logging and emitting results that will
    be streamed back to Dagster.

    This class should not be directly instantiated by the user. Instead it should be initialized by
    calling :py:func:`open_dagster_pipes()`, which will return the singleton instance of this class.
    After `open_dagster_pipes()` has been called, the singleton instance can also be retrieved by
    calling :py:func:`PipesContext.get`.
    """

    _instance: ClassVar[Optional["PipesContext"]] = None

    @classmethod
    def is_initialized(cls) -> bool:
        """bool: Whether the context has been initialized."""
        return cls._instance is not None

    @classmethod
    def set(cls, context: "PipesContext") -> None:
        """Set the singleton instance of the context."""
        cls._instance = context

    @classmethod
    def get(cls) -> "PipesContext":
        """Get the singleton instance of the context. Raises an error if the context has not been initialized."""
        if cls._instance is None:
            raise Exception(
                "PipesContext has not been initialized. You must call `open_dagster_pipes()`."
            )
        return cls._instance

    def __init__(
        self,
        params_loader: PipesParamsLoader,
        context_loader: PipesContextLoader,
        message_writer: PipesMessageWriter,
    ) -> None:
        context_params = params_loader.load_context_params()
        messages_params = params_loader.load_messages_params()
        self._io_stack = ExitStack()
        self._data = self._io_stack.enter_context(context_loader.load_context(context_params))
        self._message_channel = self._io_stack.enter_context(message_writer.open(messages_params))
        self._logger = _PipesLogger(self)
        self._materialized_assets: Set[str] = set()
        self._closed: bool = False

    def __enter__(self) -> "PipesContext":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the pipes connection. This will flush all buffered messages to the orchestration
        process and cause any further attempt to write a message to raise an error. This method is
        idempotent-- subsequent calls after the first have no effect.
        """
        if not self._closed:
            self._io_stack.close()
            self._closed = True

    @property
    def is_closed(self) -> bool:
        """bool: Whether the context has been closed."""
        return self._closed

    def _write_message(self, method: str, params: Optional[Mapping[str, Any]] = None) -> None:
        if self._closed:
            raise DagsterPipesError("Cannot send message after pipes context is closed.")
        message = _make_message(method, params)
        self._message_channel.write_message(message)

    # ########################
    # ##### PUBLIC API
    # ########################

    @property
    def is_asset_step(self) -> bool:
        """bool: Whether the current step targets assets."""
        return self._data["asset_keys"] is not None

    @property
    def asset_key(self) -> str:
        """str: The AssetKey for the currently scoped asset. Raises an error if 0 or multiple assets
        are in scope.
        """
        asset_keys = _assert_defined_asset_property(self._data["asset_keys"], "asset_key")
        _assert_single_asset(self._data, "asset_key")
        return asset_keys[0]

    @property
    def asset_keys(self) -> Sequence[str]:
        """Sequence[str]: The AssetKeys for the currently scoped assets. Raises an error if no
        assets are in scope.
        """
        asset_keys = _assert_defined_asset_property(self._data["asset_keys"], "asset_keys")
        return asset_keys

    @property
    def provenance(self) -> Optional[PipesDataProvenance]:
        """Optional[PipesDataProvenance]: The provenance for the currently scoped asset. Raises an
        error if 0 or multiple assets are in scope.
        """
        provenance_by_asset_key = _assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance"
        )
        _assert_single_asset(self._data, "provenance")
        return next(iter(provenance_by_asset_key.values()))

    @property
    def provenance_by_asset_key(self) -> Mapping[str, Optional[PipesDataProvenance]]:
        """Mapping[str, Optional[PipesDataProvenance]]: Mapping of asset key to provenance for the
        currently scoped assets. Raises an error if no assets are in scope.
        """
        provenance_by_asset_key = _assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance_by_asset_key"
        )
        return provenance_by_asset_key

    @property
    def code_version(self) -> Optional[str]:
        """Optional[str]: The code version for the currently scoped asset. Raises an error if 0 or
        multiple assets are in scope.
        """
        code_version_by_asset_key = _assert_defined_asset_property(
            self._data["code_version_by_asset_key"], "code_version"
        )
        _assert_single_asset(self._data, "code_version")
        return next(iter(code_version_by_asset_key.values()))

    @property
    def code_version_by_asset_key(self) -> Mapping[str, Optional[str]]:
        """Mapping[str, Optional[str]]: Mapping of asset key to code version for the currently
        scoped assets. Raises an error if no assets are in scope.
        """
        code_version_by_asset_key = _assert_defined_asset_property(
            self._data["code_version_by_asset_key"], "code_version_by_asset_key"
        )
        return code_version_by_asset_key

    @property
    def is_partition_step(self) -> bool:
        """bool: Whether the current step is scoped to one or more partitions."""
        return self._data["partition_key_range"] is not None

    @property
    def partition_key(self) -> str:
        """str: The partition key for the currently scoped partition. Raises an error if 0 or
        multiple partitions are in scope.
        """
        partition_key = _assert_defined_partition_property(
            self._data["partition_key"], "partition_key"
        )
        return partition_key

    @property
    def partition_key_range(self) -> "PipesPartitionKeyRange":
        """PipesPartitionKeyRange: The partition key range for the currently scoped partition or
        partitions. Raises an error if no partitions are in scope.
        """
        partition_key_range = _assert_defined_partition_property(
            self._data["partition_key_range"], "partition_key_range"
        )
        return partition_key_range

    @property
    def partition_time_window(self) -> Optional["PipesTimeWindow"]:
        """Optional[PipesTimeWindow]: The partition time window for the currently scoped partition
        or partitions. Returns None if partitions in scope are not temporal. Raises an error if no
        partitions are in scope.
        """
        # None is a valid value for partition_time_window, but we check that a partition key range
        # is defined.
        _assert_defined_partition_property(
            self._data["partition_key_range"], "partition_time_window"
        )
        return self._data["partition_time_window"]

    @property
    def run_id(self) -> str:
        """str: The run ID for the currently executing pipeline run."""
        return self._data["run_id"]

    @property
    def job_name(self) -> Optional[str]:
        """Optional[str]: The job name for the currently executing run. Returns None if the run is
        not derived from a job.
        """
        return self._data["job_name"]

    @property
    def retry_number(self) -> int:
        """int: The retry number for the currently executing run."""
        return self._data["retry_number"]

    def get_extra(self, key: str) -> Any:
        """Get the value of an extra provided by the user. Raises an error if the extra is not defined.

        Args:
            key (str): The key of the extra.

        Returns:
            Any: The value of the extra.
        """
        return _assert_defined_extra(self._data["extras"], key)

    @property
    def extras(self) -> Mapping[str, Any]:
        """Mapping[str, Any]: Key-value map for all extras provided by the user."""
        return self._data["extras"]

    # ##### WRITE

    def report_asset_materialization(
        self,
        metadata: Optional[Mapping[str, Union[PipesMetadataRawValue, PipesMetadataValue]]] = None,
        data_version: Optional[str] = None,
        asset_key: Optional[str] = None,
    ) -> None:
        """Report to Dagster that an asset has been materialized. Streams a payload containing
        materialization information back to Dagster. If no assets are in scope, raises an error.

        Args:
            metadata (Optional[Mapping[str, Union[PipesMetadataRawValue, PipesMetadataValue]]]):
                Metadata for the materialized asset. Defaults to None.
            data_version (Optional[str]): The data version for the materialized asset.
                Defaults to None.
            asset_key (Optional[str]): The asset key for the materialized asset. If only a
                single asset is in scope, default to that asset's key. If multiple assets are in scope,
                this must be set explicitly or an error will be raised.
        """
        asset_key = _resolve_optionally_passed_asset_key(
            self._data, asset_key, "report_asset_materialization"
        )
        if asset_key in self._materialized_assets:
            raise DagsterPipesError(
                f"Calling `report_asset_materialization` with asset key `{asset_key}` is undefined."
                " Asset has already been materialized, so no additional data can be reported"
                " for it."
            )
        metadata = (
            _normalize_param_metadata(metadata, "report_asset_materialization", "metadata")
            if metadata
            else None
        )
        data_version = _assert_opt_param_type(
            data_version, str, "report_asset_materialization", "data_version"
        )
        self._write_message(
            "report_asset_materialization",
            {"asset_key": asset_key, "data_version": data_version, "metadata": metadata},
        )
        self._materialized_assets.add(asset_key)

    def report_asset_check(
        self,
        check_name: str,
        passed: bool,
        severity: PipesAssetCheckSeverity = "ERROR",
        metadata: Optional[Mapping[str, Union[PipesMetadataRawValue, PipesMetadataValue]]] = None,
        asset_key: Optional[str] = None,
    ) -> None:
        """Report to Dagster that an asset check has been performed. Streams a payload containing
        check result information back to Dagster. If no assets or associated checks are in scope, raises an error.

        Args:
            check_name (str): The name of the check.
            passed (bool): Whether the check passed.
            severity (PipesAssetCheckSeverity): The severity of the check. Defaults to "ERROR".
            metadata (Optional[Mapping[str, Union[PipesMetadataRawValue, PipesMetadataValue]]]):
                Metadata for the check. Defaults to None.
            asset_key (Optional[str]): The asset key for the check. If only a single asset is in
                scope, default to that asset's key. If multiple assets are in scope, this must be
                set explicitly or an error will be raised.
        """
        asset_key = _resolve_optionally_passed_asset_key(
            self._data, asset_key, "report_asset_check"
        )
        check_name = _assert_param_type(check_name, str, "report_asset_check", "check_name")
        passed = _assert_param_type(passed, bool, "report_asset_check", "passed")
        metadata = (
            _normalize_param_metadata(metadata, "report_asset_check", "metadata")
            if metadata
            else None
        )
        self._write_message(
            "report_asset_check",
            {
                "asset_key": asset_key,
                "check_name": check_name,
                "passed": passed,
                "metadata": metadata,
                "severity": severity,
            },
        )

    @property
    def log(self) -> logging.Logger:
        """logging.Logger: A logger that streams log messages back to Dagster."""
        return self._logger
