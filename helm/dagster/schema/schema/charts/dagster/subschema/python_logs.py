from enum import Enum
from typing import Any

from pydantic import BaseModel


class PythonLogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARN = "WARN"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class PythonLogs(BaseModel, extra="forbid"):
    pythonLogLevel: PythonLogLevel | None = None
    managedPythonLoggers: list[str] | None = None
    dagsterHandlerConfig: dict[str, Any] | None = None
