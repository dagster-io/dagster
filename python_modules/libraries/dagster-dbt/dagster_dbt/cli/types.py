from collections import namedtuple
from typing import Any, Dict, Optional

from dagster import check, usable_as_dagster_type

from ..types import DbtResult


@usable_as_dagster_type
class DbtCliOutput(
    namedtuple(
        "_DbtCliOutput",
        "result command return_code raw_output num_pass num_warn num_error num_skip num_total",
    ),
):
    """The results of executing a dbt command, along with additional metadata about the dbt CLI
    process that was run.

    Note that users should not construct instances of this class directly. This class is intended
    to be constructed from the JSON output of dbt commands.

    If the executed dbt command is either ``run`` or ``test``, then the ``.num_*`` attributes will
    contain non-``None`` integer values. Otherwise, they will be ``None``.

    Attributes:
        command (str): The full shell command that was executed.
        return_code (int): The return code of the dbt CLI process.
        raw_output (str): The raw output (``stdout``) of the dbt CLI process.
        num_pass (Optional[int]): The number of dbt nodes (models) that passed.
        num_warn (Optional[int]): The number of dbt nodes (models) that emitted warnings.
        num_error (Optional[int]): The number of dbt nodes (models) that emitted errors.
        num_skip (Optional[int]): The number of dbt nodes (models) that were skipped.
        num_total (Optional[int]): The total number of dbt nodes (models) that were processed.
    """

    def __new__(
        cls,
        result: DbtResult,
        command: str,
        return_code: int,
        raw_output: str,
        num_pass: Optional[int] = None,
        num_warn: Optional[int] = None,
        num_error: Optional[int] = None,
        num_skip: Optional[int] = None,
        num_total: Optional[int] = None,
    ):
        return super().__new__(
            cls,
            result,
            check.str_param(command, "command"),
            check.int_param(return_code, "return_code"),
            check.str_param(raw_output, "raw_output"),
            check.opt_int_param(num_pass, "num_pass"),
            check.opt_int_param(num_warn, "num_warn"),
            check.opt_int_param(num_error, "num_error"),
            check.opt_int_param(num_skip, "num_skip"),
            check.opt_int_param(num_total, "num_total"),
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DbtCliOutput":
        """Constructs an instance of :class:`DbtCliOutput <dagster_dbt.DbtCliOutput>` from a
        dictionary.

        Args:
            d (Dict[str, Any]): A dictionary with key-values to construct a :class:`DbtCliOutput
                <dagster_dbt.DbtCliOutput>`.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput <dagster_dbt.DbtCliOutput>`.
        """
        return_code = check.int_elem(d, "return_code")
        raw_output = check.str_elem(d, "raw_output")
        num_pass = check.opt_int_elem(d, "num_pass")
        num_warn = check.opt_int_elem(d, "num_warn")
        num_error = check.opt_int_elem(d, "num_error")
        num_skip = check.opt_int_elem(d, "num_skip")
        num_total = check.opt_int_elem(d, "num_total")
        command = check.str_elem(d, "command")

        return cls(
            result=DbtResult.from_dict(d),
            return_code=return_code,
            raw_output=raw_output,
            num_pass=num_pass,
            num_warn=num_warn,
            num_error=num_error,
            num_skip=num_skip,
            num_total=num_total,
            command=command,
        )
