from typing import Any, Dict, List, Optional

from pydantic import BaseModel  # pylint: disable=no-name-in-module


class PythonLogs(BaseModel):
    pythonLogLevel: Optional[str]
    managedPythonLoggers: Optional[List[str]]
    dagsterHandlerConfig: Optional[Dict[str, Any]]
