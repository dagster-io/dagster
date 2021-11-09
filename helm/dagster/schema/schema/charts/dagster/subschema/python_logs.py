from typing import Any, Dict, List

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class PythonLogs(BaseModel):
    pythonLogLevel: str
    managedPythonLoggers: List[str]
    dagsterHandlerConfig: Dict[str, Any]
