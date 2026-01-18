from enum import Enum
from typing import Any, Optional

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
    pythonLogLevel: Optional[PythonLogLevel] = None
    managedPythonLoggers: Optional[list[str]] = None
    dagsterHandlerConfig: Optional[dict[str, Any]] = None
