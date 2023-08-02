from typing import Any, Mapping, Optional, Sequence

import dagster._check as check

from ..types import DbtOutput


class DbtCliOutput(DbtOutput):
    """The results of executing a dbt command, along with additional metadata about the dbt CLI
    process that was run.

    This class is deprecated, because it's only produced by methods of the DbtCliClientResource class,
    which is deprecated in favor of DbtCliResource.

    Note that users should not construct instances of this class directly. This class is intended
    to be constructed from the JSON output of dbt commands.

    Attributes:
        command (str): The full shell command that was executed.
        return_code (int): The return code of the dbt CLI process.
        raw_output (str): The raw output (``stdout``) of the dbt CLI process.
        logs (List[Dict[str, Any]]): List of parsed JSON logs produced by the dbt command.
        result (Optional[Dict[str, Any]]): Dictionary containing dbt-reported result information
            contained in run_results.json.  Some dbt commands do not produce results, and will
            therefore have result = None.
        docs_url (Optional[str]): Hostname where dbt docs are being served for this project.
    """

    def __init__(
        self,
        command: str,
        return_code: int,
        raw_output: str,
        logs: Sequence[Mapping[str, Any]],
        result: Mapping[str, Any],
        docs_url: Optional[str] = None,
    ):
        self._command = check.str_param(command, "command")
        self._return_code = check.int_param(return_code, "return_code")
        self._raw_output = check.str_param(raw_output, "raw_output")
        self._logs = check.sequence_param(logs, "logs", of_type=dict)
        self._docs_url = check.opt_str_param(docs_url, "docs_url")
        super().__init__(result)

    @property
    def command(self) -> str:
        return self._command

    @property
    def return_code(self) -> int:
        return self._return_code

    @property
    def raw_output(self) -> str:
        return self._raw_output

    @property
    def logs(self) -> Sequence[Mapping[str, Any]]:
        return self._logs

    @property
    def docs_url(self) -> Optional[str]:
        return self._docs_url
