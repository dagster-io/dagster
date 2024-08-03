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
            int_value if isinstance(int_value, int) else check.int_param(int_value, "int_value"),
            str_value if isinstance(str_value, str) else check.str_param(str_value, "str_value"),
        )


class ExampleDataClass(
    NamedTuple(
        "ExampleDataClass",
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
    ) -> "ExampleDataClass":
        return super().__new__(
            cls,
            int_value if isinstance(int_value, int) else check.int_param(int_value, "int_value"),
            str_value if isinstance(str_value, str) else check.str_param(str_value, "str_value"),
        )


print(ExampleDataClass(int_value=0, str_value="str"))
