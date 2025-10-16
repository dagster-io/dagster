from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from typing import IO, Any, Optional

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import public
from dagster._core.storage.compute_log_manager import (
    CapturedLogContext,
    CapturedLogMetadata,
    CapturedLogSubscription,
    ComputeIOType,
    ComputeLogManager,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData


@public
class NoOpComputeLogManager(ComputeLogManager, ConfigurableClass):
    """When enabled for a Dagster instance, stdout and stderr will not be available for any step."""

    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Generator[CapturedLogContext, None, None]:
        yield CapturedLogContext(log_key=log_key)

    def is_capture_complete(self, log_key: Sequence[str]):
        return True

    @contextmanager
    def open_log_stream(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Generator[Optional[IO], None, None]:
        yield None

    def get_log_data_for_type(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
        offset: int,
        max_bytes: Optional[int],
    ) -> tuple[Optional[bytes], int]:
        return None, 0

    def get_log_metadata(self, log_key: Sequence[str]) -> CapturedLogMetadata:
        return CapturedLogMetadata()

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        pass

    def subscribe(
        self, log_key: Sequence[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        return CapturedLogSubscription(self, log_key, cursor)

    def unsubscribe(self, subscription: CapturedLogSubscription):
        pass
