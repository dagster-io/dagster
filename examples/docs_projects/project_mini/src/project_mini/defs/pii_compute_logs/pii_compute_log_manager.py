from collections.abc import Sequence

from dagster import Bool, Field, StringSource
from dagster._core.storage.captured_log_manager import CapturedLogData
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._serdes import ConfigurableClass, ConfigurableClassData

from .pii_redactor import redact_pii


class PIIComputeLogManager(LocalComputeLogManager, ConfigurableClass):
    """A compute log manager that redacts PII from logs before displaying them."""

    def __init__(
        self,
        base_dir: str = "compute_logs",
        redact_for_ui: bool = True,
        inst_data: ConfigurableClassData | None = None,
    ):
        super().__init__(base_dir)
        self.redact_for_ui = redact_for_ui
        self._inst_data = inst_data

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "base_dir": Field(
                StringSource,
                default_value="compute_logs",
                description="Base directory for storing compute logs",
            ),
            "redact_for_ui": Field(
                Bool,
                default_value=True,
                description="Whether to redact PII for UI display",
            ),
        }

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value):
        return cls(inst_data=inst_data, **config_value)

    def _redact_bytes(self, data: bytes | None) -> bytes | None:
        """Apply PII redaction to bytes data."""
        if not data or not self.redact_for_ui:
            return data
        text = data.decode("utf-8", errors="replace")
        redacted_text = redact_pii(text)
        return redacted_text.encode("utf-8")

    # highlight-start
    def get_log_data(
        self,
        log_key: Sequence[str],
        cursor: str | None = None,
        max_bytes: int | None = None,
    ) -> CapturedLogData:
        """Override to apply PII redaction when logs are read."""
        original_data = super().get_log_data(log_key, cursor, max_bytes)

        if not self.redact_for_ui:
            return original_data

        return CapturedLogData(
            log_key=original_data.log_key,
            stdout=self._redact_bytes(original_data.stdout),
            stderr=self._redact_bytes(original_data.stderr),
            cursor=original_data.cursor,
        )

    # highlight-end

    def get_log_data_for_type(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
        offset: int,
        max_bytes: int | None,
    ) -> tuple[bytes | None, int]:
        """Override to apply PII redaction to log data chunks."""
        data, new_offset = super().get_log_data_for_type(log_key, io_type, offset, max_bytes)

        if self.redact_for_ui and data:
            return self._redact_bytes(data), new_offset

        return data, new_offset
