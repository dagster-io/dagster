import asyncio

import pytest
from dagster_shared.utils.cached_method import cached_method


@pytest.mark.parametrize("number", [0, 1, -1, 10**30])
@pytest.mark.parametrize("string_first", [False, True])
def test_cached_method_distinguishes_integer_and_string_arguments(
    number: int, string_first: bool
) -> None:
    class MyClass:
        @cached_method
        def my_method(self, value: int | str) -> dict[str, int | str]:
            return {"value": value}

    obj = MyClass()
    first, second = (str(number), number) if string_first else (number, str(number))
    first_result = obj.my_method(first)
    second_result = obj.my_method(second)

    assert first_result == {"value": first}
    assert second_result == {"value": second}
    assert first_result is not second_result
    assert obj.my_method(value=first) is first_result
    assert obj.my_method(value=second) is second_result


@pytest.mark.parametrize("number", [0, 1, -1, 10**30])
@pytest.mark.parametrize("string_first", [False, True])
def test_async_cached_method_distinguishes_integer_and_string_arguments(
    number: int, string_first: bool
) -> None:
    class MyClass:
        @cached_method
        async def my_method(self, value: int | str) -> dict[str, int | str]:
            return {"value": value}

    obj = MyClass()
    first, second = (str(number), number) if string_first else (number, str(number))
    first_result = asyncio.run(obj.my_method(first))
    second_result = asyncio.run(obj.my_method(second))

    assert first_result == {"value": first}
    assert second_result == {"value": second}
    assert first_result is not second_result
    assert asyncio.run(obj.my_method(value=first)) is first_result
    assert asyncio.run(obj.my_method(value=second)) is second_result


def test_cached_method_keeps_keyword_names_and_values_separate() -> None:
    class MyClass:
        @cached_method
        def my_method(self, **kwargs: int | str) -> dict[str, int | str]:
            return kwargs

    obj = MyClass()
    first = {"a": "b.1"}
    second = {"a.b": 1}
    first_result = obj.my_method(**first)
    second_result = obj.my_method(**second)

    assert first_result == first
    assert second_result == second
    assert first_result is not second_result
    assert obj.my_method(**first) is first_result
    assert obj.my_method(**second) is second_result
