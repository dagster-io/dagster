from enum import Enum
from typing import Any, Dict, List, Optional

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
    managedPythonLoggers: Optional[List[str]] = None
    dagsterHandlerConfig: Optional[Dict[str, Any]] = None
