from typing import NamedTuple

from dagster import _check as check


class Example(
    NamedTuple(
        "Example",
        [
            ("int_value", int),
            ("str_value", str),
        ],
    )
):
    int_value: int
    str_value: str

    def __new__(
        cls,
        *,
        int_value: int,
        str_value: str,
    ) -> "Example":
        return super().__new__(
            cls,
            check.int_param(int_value, "int_value"),
            check.str_param(str_value, "str_value"),
        )