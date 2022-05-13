from typing import Any, Dict, Optional

import dagster._check as check


class DbtOutput:
    """
    Base class for both DbtCliOutput and DbtRPCOutput. Contains a single field, `result`, which
    represents the dbt-formatted result of the command that was run (if any).

    Used internally, should not be instantiated directly by the user.
    """

    def __init__(self, result: Dict[str, Any]):
        self._result = check.dict_param(result, "result", key_type=str)

    @property
    def result(self) -> Dict[str, Any]:
        return self._result

    @property
    def docs_url(self) -> Optional[str]:
        return None
