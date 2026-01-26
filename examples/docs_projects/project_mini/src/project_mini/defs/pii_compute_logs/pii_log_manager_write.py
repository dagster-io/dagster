from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Optional

from dagster import Bool, Field, StringSource
from dagster._core.storage.captured_log_manager import CapturedLogContext
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._serdes import ConfigurableClass, ConfigurableClassData

from .pii_redactor import redact_pii


# highlight-start
class PIIRedactingStream:
    """A stream wrapper that redacts PII as data is written."""

    def __init__(self, original_stream, encoding: str = "utf-8"):
        self.original = original_stream
        self.encoding = encoding

    def write(self, data):
        if isinstance(data, bytes):
            text = data.decode(self.encoding, errors="replace")
            redacted = redact_pii(text)
            return self.original.write(redacted.encode(self.encoding))
        elif isinstance(data, str) and data.strip():
            redacted = redact_pii(data)
            return self.original.write(redacted)
        return self.original.write(data)

    def flush(self):
        return self.original.flush()

    def fileno(self):
        return self.original.fileno()


# highlight-end


class PIIComputeLogManagerWrite(LocalComputeLogManager, ConfigurableClass):
    """A compute log manager that redacts PII when logs are written to disk."""

    def __init__(
        self,
        base_dir: str = "compute_logs",
        redact_on_write: bool = True,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        super().__init__(base_dir)
        self.redact_on_write = redact_on_write
        self._inst_data = inst_data

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "base_dir": Field(
                StringSource,
                default_value="compute_logs",
                description="Base directory for storing compute logs",
            ),
            "redact_on_write": Field(
                Bool,
                default_value=True,
                description="Whether to redact PII when writing logs",
            ),
        }

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value):
        return cls(inst_data=inst_data, **config_value)

    # highlight-start
    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Iterator[CapturedLogContext]:
        """Override capture_logs to wrap streams with PII redaction."""
        with super().capture_logs(log_key) as context:
            if self.redact_on_write:
                # Wrap the output streams with PII-redacting wrappers
                original_out = context.out_fd
                original_err = context.err_fd

                context._out_fd = PIIRedactingStream(original_out)  # noqa: SLF001
                context._err_fd = PIIRedactingStream(original_err)  # noqa: SLF001

            yield context

    # highlight-end
