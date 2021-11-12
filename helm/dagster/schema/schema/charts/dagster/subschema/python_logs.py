from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class PythonLogLevel(Enum):
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARN = "WARN"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class PythonLogs(BaseModel):
    pythonLogLevel: Optional[PythonLogLevel]
    managedPythonLoggers: Optional[List[str]]
    dagsterHandlerConfig: Optional[Dict[str, Any]]
