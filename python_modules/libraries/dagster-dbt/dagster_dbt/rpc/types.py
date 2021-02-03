from collections import namedtuple
from typing import Any, Dict

from dagster import check, usable_as_dagster_type

from ..types import DbtResult


@usable_as_dagster_type
class DbtRpcOutput(namedtuple("_DbtRpcOutput", "result state start end elapsed")):
    """The output from executing a dbt command via the dbt RPC server.

    Note that users should not construct instances of this class directly. This class is intended to be
    constructed from the JSON output of dbt commands.

    Attributes:
        result (DbtResult): The dbt results from the executed command.
        state (str): The state of the polled dbt process.
        start (str): An ISO string timestamp of when the dbt process started.
        end (str): An ISO string timestamp of when the dbt process ended.
        elapsed (float): The duration (in seconds) for which the dbt process was running.
    """

    def __new__(
        cls,
        result: DbtResult,
        state: str,
        start: str,
        end: str,
        elapsed: float,
    ):
        return super().__new__(
            cls,
            result,
            check.str_param(state, "state"),
            check.str_param(start, "start"),
            check.str_param(end, "end"),
            check.float_param(elapsed, "elapsed"),
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DbtRpcOutput":
        """Constructs an instance of :class:`DbtRpcOutput <dagster_dbt.DbtRpcOutput>` from a
        dictionary.

        Args:
            d (Dict[str, Any]): A dictionary with key-values to construct a :class:`DbtRpcOutput
                <dagster_dbt.DbtRpcOutput>`.

        Returns:
            DbtRpcOutput: An instance of :class:`DbtRpcOutput <dagster_dbt.DbtRpcOutput>`.
        """
        state = check.str_elem(d, "state")
        start = check.str_elem(d, "start")
        end = check.str_elem(d, "end")
        elapsed = check.float_elem(d, "elapsed")

        result = DbtResult.from_dict(d)

        return cls(result=result, state=state, start=start, end=end, elapsed=elapsed)
