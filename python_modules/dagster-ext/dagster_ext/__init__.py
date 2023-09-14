import atexit
import base64
import datetime
import json
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
    Generic,
    Iterator,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TextIO,
    Type,
    TypedDict,
    TypeVar,
    cast,
    get_args,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

# ########################
# ##### PROTOCOL
# ########################


ExtExtras = Mapping[str, Any]
ExtParams = Mapping[str, Any]


_ENV_KEY_PREFIX = "DAGSTER_EXT_"


def _param_name_to_env_key(key: str) -> str:
    return f"{_ENV_KEY_PREFIX}{key.upper()}"


# ##### PARAMETERS

IS_DAGSTER_EXT_PROCESS_ENV_VAR = "IS_DAGSTER_EXT_PROCESS"

DAGSTER_EXT_ENV_KEYS = {
    k: _param_name_to_env_key(k) for k in (IS_DAGSTER_EXT_PROCESS_ENV_VAR, "context", "messages")
}


# ##### MESSAGE


class ExtMessage(TypedDict):
    method: str
    params: Optional[Mapping[str, Any]]


# ##### EXTERNAL EXECUTION CONTEXT


class ExtContextData(TypedDict):
    asset_keys: Optional[Sequence[str]]
    code_version_by_asset_key: Optional[Mapping[str, Optional[str]]]
    provenance_by_asset_key: Optional[Mapping[str, Optional["ExtDataProvenance"]]]
    partition_key: Optional[str]
    partition_key_range: Optional["ExtPartitionKeyRange"]
    partition_time_window: Optional["ExtTimeWindow"]
    run_id: str
    job_name: Optional[str]
    retry_number: int
    extras: Mapping[str, Any]


class ExtPartitionKeyRange(TypedDict):
    start: str
    end: str


class ExtTimeWindow(TypedDict):
    start: str  # timestamp
    end: str  # timestamp


class ExtDataProvenance(TypedDict):
    code_version: str
    input_data_versions: Mapping[str, str]
    is_user_provided: bool


ExtMetadataType = Literal[
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


class DagsterExtError(Exception):
    pass


class DagsterExtWarning(Warning):
    pass


def _assert_not_none(value: Optional[_T], desc: Optional[str] = None) -> _T:
    if value is None:
        raise DagsterExtError(f"Missing required property: {desc}")
    return value


def _assert_defined_asset_property(value: Optional[_T], key: str) -> _T:
    return _assert_not_none(value, f"`{key}` is undefined. Current step does not target an asset.")


# This should only be called under the precondition that the current step targets assets.
def _assert_single_asset(data: ExtContextData, key: str) -> None:
    asset_keys = data["asset_keys"]
    assert asset_keys is not None
    if len(asset_keys) != 1:
        raise DagsterExtError(f"`{key}` is undefined. Current step targets multiple assets.")


def _resolve_optionally_passed_asset_key(
    data: ExtContextData, asset_key: Optional[str], method: str
) -> str:
    asset_keys = _assert_defined_asset_property(data["asset_keys"], method)
    asset_key = _assert_opt_param_type(asset_key, str, method, "asset_key")
    if asset_key and asset_key not in asset_keys:
        raise DagsterExtError(
            f"Invalid asset key. Expected one of `{asset_keys}`, got `{asset_key}`."
        )
    if not asset_key:
        if len(asset_keys) != 1:
            raise DagsterExtError(
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
def _assert_single_partition(data: ExtContextData, key: str) -> None:
    partition_key_range = data["partition_key_range"]
    assert partition_key_range is not None
    if partition_key_range["start"] != partition_key_range["end"]:
        raise DagsterExtError(f"`{key}` is undefined. Current step targets multiple partitions.")


def _assert_defined_extra(extras: ExtExtras, key: str) -> Any:
    if key not in extras:
        raise DagsterExtError(f"Extra `{key}` is undefined. Extras must be provided by user.")
    return extras[key]


def _assert_param_type(value: _T, expected_type: Any, method: str, param: str) -> _T:
    if not isinstance(value, expected_type):
        raise DagsterExtError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected `{expected_type}`, got"
            f" `{type(value)}`."
        )
    return value


def _assert_opt_param_type(value: _T, expected_type: Any, method: str, param: str) -> _T:
    if not (isinstance(value, expected_type) or value is None):
        raise DagsterExtError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected"
            f" `Optional[{expected_type}]`, got `{type(value)}`."
        )
    return value


def _assert_env_param_type(
    env_params: ExtParams, key: str, expected_type: Type[_T], cls: Type
) -> _T:
    value = env_params.get(key)
    if not isinstance(value, expected_type):
        raise DagsterExtError(
            f"Invalid type for parameter `{key}` passed from orchestration side to"
            f" `{cls.__name__}`. Expected `{expected_type}`, got `{type(value)}`."
        )
    return value


def _assert_opt_env_param_type(
    env_params: ExtParams, key: str, expected_type: Type[_T], cls: Type
) -> Optional[_T]:
    value = env_params.get(key)
    if value is not None and not isinstance(value, expected_type):
        raise DagsterExtError(
            f"Invalid type for parameter `{key}` passed from orchestration side to"
            f" `{cls.__name__}`. Expected `Optional[{expected_type}]`, got `{type(value)}`."
        )
    return value


def _assert_param_value(value: _T, expected_values: Sequence[_T], method: str, param: str) -> _T:
    if value not in expected_values:
        raise DagsterExtError(
            f"Invalid value for parameter `{param}` of `{method}`. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def _assert_opt_param_value(
    value: _T, expected_values: Sequence[_T], method: str, param: str
) -> _T:
    if value is not None and value not in expected_values:
        raise DagsterExtError(
            f"Invalid value for parameter `{param}` of `{method}`. Expected one of"
            f" `{expected_values}`, got `{value}`."
        )
    return value


def _assert_param_json_serializable(value: _T, method: str, param: str) -> _T:
    try:
        json.dumps(value)
    except (TypeError, OverflowError):
        raise DagsterExtError(
            f"Invalid type for parameter `{param}` of `{method}`. Expected a JSON-serializable"
            f" type, got `{type(value)}`."
        )
    return value


def _param_from_env_var(key: str) -> Any:
    raw_value = os.environ.get(_param_name_to_env_var(key))
    return decode_env_var(raw_value) if raw_value is not None else None


def encode_env_var(value: Any) -> str:
    serialized = json.dumps(value)
    compressed = zlib.compress(serialized.encode("utf-8"))
    encoded = base64.b64encode(compressed)
    return encoded.decode("utf-8")  # as string


def decode_env_var(value: Any) -> str:
    decoded = base64.b64decode(value)
    decompressed = zlib.decompress(decoded)
    return json.loads(decompressed.decode("utf-8"))


def _param_name_to_env_var(param_name: str) -> str:
    return f"{_ENV_KEY_PREFIX}{param_name.upper()}"


def _env_var_to_param_name(env_var: str) -> str:
    return env_var[len(_ENV_KEY_PREFIX) :].lower()


def is_dagster_ext_process() -> bool:
    return _param_from_env_var(IS_DAGSTER_EXT_PROCESS_ENV_VAR)


def _emit_orchestration_inactive_warning() -> None:
    warnings.warn(
        "This process was not launched by a Dagster orchestration process. All calls to the"
        " `dagster-ext` context or attempts to initialize `dagster-ext` abstractions"
        " are no-ops.",
        category=DagsterExtWarning,
    )


def _get_mock() -> "MagicMock":
    from unittest.mock import MagicMock

    return MagicMock()


# ########################
# ##### IO - BASE
# ########################


class ExtContextLoader(ABC):
    @abstractmethod
    @contextmanager
    def load_context(self, params: ExtParams) -> Iterator[ExtContextData]:
        ...


T_MessageChannel = TypeVar("T_MessageChannel", bound="ExtMessageWriterChannel")


class ExtMessageWriter(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    @contextmanager
    def open(self, params: ExtParams) -> Iterator[T_MessageChannel]:
        ...


class ExtMessageWriterChannel(ABC, Generic[T_MessageChannel]):
    @abstractmethod
    def write_message(self, message: ExtMessage) -> None:
        ...


class ExtParamLoader(ABC):
    @abstractmethod
    def load_context_params(self) -> ExtParams:
        ...

    @abstractmethod
    def load_messages_params(self) -> ExtParams:
        ...


T_BlobStoreMessageWriterChannel = TypeVar(
    "T_BlobStoreMessageWriterChannel", bound="ExtBlobStoreMessageWriterChannel"
)


class ExtBlobStoreMessageWriter(ExtMessageWriter[T_BlobStoreMessageWriterChannel]):
    def __init__(self, *, interval: float = 10):
        self.interval = interval

    @contextmanager
    def open(self, params: ExtParams) -> Iterator[T_BlobStoreMessageWriterChannel]:
        channel = self.make_channel(params)
        with channel.buffered_upload_loop():
            yield channel

    @abstractmethod
    def make_channel(self, params: ExtParams) -> T_BlobStoreMessageWriterChannel:
        ...


class ExtBlobStoreMessageWriterChannel(ExtMessageWriterChannel):
    def __init__(self, *, interval: float = 10):
        self._interval = interval
        self._lock = Lock()
        self._buffer = []
        self._counter = 1

    def write_message(self, message: ExtMessage) -> None:
        with self._lock:
            self._buffer.append(message)

    def flush_messages(self) -> Sequence[ExtMessage]:
        with self._lock:
            messages = list(self._buffer)
            self._buffer.clear()
            return messages

    @abstractmethod
    def upload_messages_chunk(self, payload: StringIO, index: int) -> None:
        ...

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


class ExtBufferedFilesystemMessageWriterChannel(ExtBlobStoreMessageWriterChannel):
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


class ExtDefaultContextLoader(ExtContextLoader):
    FILE_PATH_KEY = "path"
    DIRECT_KEY = "data"

    @contextmanager
    def load_context(self, params: ExtParams) -> Iterator[ExtContextData]:
        if self.FILE_PATH_KEY in params:
            path = _assert_env_param_type(params, self.FILE_PATH_KEY, str, self.__class__)
            with open(path, "r") as f:
                data = json.load(f)
                yield data
        elif self.DIRECT_KEY in params:
            data = _assert_env_param_type(params, self.DIRECT_KEY, dict, self.__class__)
            yield cast(ExtContextData, data)
        else:
            raise DagsterExtError(
                f'Invalid params for {self.__class__.__name__}, expected key "{self.FILE_PATH_KEY}"'
                f' or "{self.DIRECT_KEY}", received {params}',
            )


class ExtDefaultMessageWriter(ExtMessageWriter):
    FILE_PATH_KEY = "path"
    STDIO_KEY = "stdio"
    STDERR = "stderr"
    STDOUT = "stdout"

    @contextmanager
    def open(self, params: ExtParams) -> Iterator[ExtMessageWriterChannel]:
        if self.FILE_PATH_KEY in params:
            path = _assert_env_param_type(params, self.FILE_PATH_KEY, str, self.__class__)
            yield ExtFileMessageWriterChannel(path)
        elif self.STDIO_KEY in params:
            stream = _assert_env_param_type(params, self.STDIO_KEY, str, self.__class__)
            if stream == self.STDERR:
                yield ExtStreamMessageWriterChannel(sys.stderr)
            elif stream == self.STDOUT:
                yield ExtStreamMessageWriterChannel(sys.stdout)
            else:
                raise DagsterExtError(
                    f'Invalid value for key "std", expected "{self.STDERR}" or "{self.STDOUT}" but'
                    f" received {stream}"
                )
        else:
            raise DagsterExtError(
                f'Invalid params for {self.__class__.__name__}, expected key "path" or "std",'
                f" received {params}"
            )


class ExtFileMessageWriterChannel(ExtMessageWriterChannel):
    def __init__(self, path: str):
        self._path = path

    def write_message(self, message: ExtMessage) -> None:
        with open(self._path, "a") as f:
            f.write(json.dumps(message) + "\n")


class ExtStreamMessageWriterChannel(ExtMessageWriterChannel):
    def __init__(self, stream: TextIO):
        self._stream = stream

    def write_message(self, message: ExtMessage) -> None:
        self._stream.writelines((json.dumps(message), "\n"))


class ExtEnvVarParamLoader(ExtParamLoader):
    def load_context_params(self) -> ExtParams:
        return _param_from_env_var("context")

    def load_messages_params(self) -> ExtParams:
        return _param_from_env_var("messages")


# ########################
# ##### IO - S3
# ########################


class ExtS3MessageWriter(ExtBlobStoreMessageWriter):
    # client is a boto3.client("s3") object
    def __init__(self, client: Any, *, interval: float = 10):
        super().__init__(interval=interval)
        # Not checking client type for now because it's a boto3.client object and we don't want to
        # depend on boto3.
        self._client = client

    def make_channel(
        self,
        params: ExtParams,
    ) -> "ExtS3MessageChannel":
        bucket = _assert_env_param_type(params, "bucket", str, self.__class__)
        key_prefix = _assert_opt_env_param_type(params, "key_prefix", str, self.__class__)
        return ExtS3MessageChannel(
            client=self._client,
            bucket=bucket,
            key_prefix=key_prefix,
            interval=self.interval,
        )


class ExtS3MessageChannel(ExtBlobStoreMessageWriterChannel):
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


class ExtDbfsContextLoader(ExtContextLoader):
    @contextmanager
    def load_context(self, params: ExtParams) -> Iterator[ExtContextData]:
        unmounted_path = _assert_env_param_type(params, "path", str, self.__class__)
        path = os.path.join("/dbfs", unmounted_path.lstrip("/"))
        with open(path, "r") as f:
            yield json.load(f)


class ExtDbfsMessageWriter(ExtBlobStoreMessageWriter):
    def make_channel(
        self,
        params: ExtParams,
    ) -> "ExtBufferedFilesystemMessageWriterChannel":
        unmounted_path = _assert_env_param_type(params, "path", str, self.__class__)
        return ExtBufferedFilesystemMessageWriterChannel(
            path=os.path.join("/dbfs", unmounted_path.lstrip("/")),
            interval=self.interval,
        )


# ########################
# ##### CONTEXT
# ########################


def init_dagster_ext(
    *,
    context_loader: Optional[ExtContextLoader] = None,
    message_writer: Optional[ExtMessageWriter] = None,
    param_loader: Optional[ExtParamLoader] = None,
) -> "ExtContext":
    if ExtContext.is_initialized():
        return ExtContext.get()

    if is_dagster_ext_process():
        param_loader = param_loader or ExtEnvVarParamLoader()
        context_params = param_loader.load_context_params()
        messages_params = param_loader.load_messages_params()
        context_loader = context_loader or ExtDefaultContextLoader()
        message_writer = message_writer or ExtDefaultMessageWriter()
        stack = ExitStack()
        context_data = stack.enter_context(context_loader.load_context(context_params))
        message_channel = stack.enter_context(message_writer.open(messages_params))
        atexit.register(stack.__exit__, None, None, None)
        context = ExtContext(context_data, message_channel)
    else:
        _emit_orchestration_inactive_warning()
        context = _get_mock()
    ExtContext.set(context)
    return context


class ExtContext:
    _instance: ClassVar[Optional["ExtContext"]] = None

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._instance is not None

    @classmethod
    def set(cls, context: "ExtContext") -> None:
        cls._instance = context

    @classmethod
    def get(cls) -> "ExtContext":
        if cls._instance is None:
            raise Exception(
                "ExtContext has not been initialized. You must call `init_dagster_ext()`."
            )
        return cls._instance

    def __init__(
        self,
        data: ExtContextData,
        message_channel: ExtMessageWriterChannel,
    ) -> None:
        self._data = data
        self.message_channel = message_channel

    def _write_message(self, method: str, params: Optional[Mapping[str, Any]] = None) -> None:
        message = ExtMessage(method=method, params=params)
        self.message_channel.write_message(message)

    # ########################
    # ##### PUBLIC API
    # ########################

    @property
    def is_asset_step(self) -> bool:
        return self._data["asset_keys"] is not None

    @property
    def asset_key(self) -> str:
        asset_keys = _assert_defined_asset_property(self._data["asset_keys"], "asset_key")
        _assert_single_asset(self._data, "asset_key")
        return asset_keys[0]

    @property
    def asset_keys(self) -> Sequence[str]:
        asset_keys = _assert_defined_asset_property(self._data["asset_keys"], "asset_keys")
        return asset_keys

    @property
    def provenance(self) -> Optional[ExtDataProvenance]:
        provenance_by_asset_key = _assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance"
        )
        _assert_single_asset(self._data, "provenance")
        return list(provenance_by_asset_key.values())[0]

    @property
    def provenance_by_asset_key(self) -> Mapping[str, Optional[ExtDataProvenance]]:
        provenance_by_asset_key = _assert_defined_asset_property(
            self._data["provenance_by_asset_key"], "provenance_by_asset_key"
        )
        return provenance_by_asset_key

    @property
    def code_version(self) -> Optional[str]:
        code_version_by_asset_key = _assert_defined_asset_property(
            self._data["code_version_by_asset_key"], "code_version"
        )
        _assert_single_asset(self._data, "code_version")
        return list(code_version_by_asset_key.values())[0]

    @property
    def code_version_by_asset_key(self) -> Mapping[str, Optional[str]]:
        code_version_by_asset_key = _assert_defined_asset_property(
            self._data["code_version_by_asset_key"], "code_version_by_asset_key"
        )
        return code_version_by_asset_key

    @property
    def is_partition_step(self) -> bool:
        return self._data["partition_key_range"] is not None

    @property
    def partition_key(self) -> str:
        partition_key = _assert_defined_partition_property(
            self._data["partition_key"], "partition_key"
        )
        return partition_key

    @property
    def partition_key_range(self) -> Optional["ExtPartitionKeyRange"]:
        partition_key_range = _assert_defined_partition_property(
            self._data["partition_key_range"], "partition_key_range"
        )
        return partition_key_range

    @property
    def partition_time_window(self) -> Optional["ExtTimeWindow"]:
        # None is a valid value for partition_time_window, but we check that a partition key range
        # is defined.
        _assert_defined_partition_property(
            self._data["partition_key_range"], "partition_time_window"
        )
        return self._data["partition_time_window"]

    @property
    def run_id(self) -> str:
        return self._data["run_id"]

    @property
    def job_name(self) -> Optional[str]:
        return self._data["job_name"]

    @property
    def retry_number(self) -> int:
        return self._data["retry_number"]

    def get_extra(self, key: str) -> Any:
        return _assert_defined_extra(self._data["extras"], key)

    @property
    def extras(self) -> Mapping[str, Any]:
        return self._data["extras"]

    # ##### WRITE

    def report_asset_metadata(
        self,
        label: str,
        value: Any,
        metadata_type: Optional[ExtMetadataType] = None,
        asset_key: Optional[str] = None,
    ) -> None:
        asset_key = _resolve_optionally_passed_asset_key(
            self._data, asset_key, "report_asset_metadata"
        )
        label = _assert_param_type(label, str, "report_asset_metadata", "label")
        value = _assert_param_json_serializable(value, "report_asset_metadata", "value")
        metadata_type = _assert_opt_param_value(
            metadata_type, get_args(ExtMetadataType), "report_asset_metadata", "type"
        )
        self._write_message(
            "report_asset_metadata",
            {"asset_key": asset_key, "label": label, "value": value, "type": metadata_type},
        )

    def report_asset_data_version(self, data_version: str, asset_key: Optional[str] = None) -> None:
        asset_key = _resolve_optionally_passed_asset_key(
            self._data, asset_key, "report_asset_data_version"
        )
        data_version = _assert_param_type(
            data_version, str, "report_asset_data_version", "data_version"
        )
        self._write_message(
            "report_asset_data_version", {"asset_key": asset_key, "data_version": data_version}
        )

    def log(self, message: str, level: str = "info") -> None:
        message = _assert_param_type(message, str, "log", "asset_key")
        level = _assert_param_value(level, ["info", "warning", "error"], "log", "level")
        self._write_message("log", {"message": message, "level": level})
