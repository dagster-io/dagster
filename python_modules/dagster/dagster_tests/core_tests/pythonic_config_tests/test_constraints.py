from typing import List

import pytest
from dagster._config.pythonic_config import Config
from pydantic import Field, ValidationError, conlist, constr


def test_str_min_length() -> None:
    class AStringConfig(Config):
        a_str: str = Field(min_length=2, max_length=10)

    AStringConfig(a_str="foo")
    with pytest.raises(ValidationError, match=" at least 2 characters"):
        AStringConfig(a_str="f")
    with pytest.raises(ValidationError, match=" at most 10 characters"):
        AStringConfig(a_str="foofoofoofoofoo")


def test_str_regex() -> None:
    try:

        class AStringConfig(Config):  # type: ignore
            a_str: str = Field(regex=r"^(foo)+$")

    except:

        class AStringConfig(Config):
            a_str: str = Field(pattern=r"^(foo)+$")

    AStringConfig(a_str="foo")
    AStringConfig(a_str="foofoofoo")
    with pytest.raises(ValidationError, match="match"):
        AStringConfig(a_str="bar")


def test_int_gtlt() -> None:
    class AnIntConfig(Config):
        an_int: int = Field(gt=0, lt=10)

    AnIntConfig(an_int=5)
    with pytest.raises(ValidationError, match=" less than 10"):
        AnIntConfig(an_int=10)
    with pytest.raises(ValidationError, match=" greater than 0"):
        AnIntConfig(an_int=0)


def test_int_gele() -> None:
    class AnIntConfig(Config):
        an_int: int = Field(ge=0, le=10)

    AnIntConfig(an_int=5)
    AnIntConfig(an_int=10)
    AnIntConfig(an_int=0)
    with pytest.raises(ValidationError, match=" less than or equal to 10"):
        AnIntConfig(an_int=11)
    with pytest.raises(ValidationError, match=" greater than or equal to 0"):
        AnIntConfig(an_int=-1)


def test_int_multiple() -> None:
    class AnIntConfig(Config):
        an_int: int = Field(multiple_of=5)

    AnIntConfig(an_int=5)
    AnIntConfig(an_int=10)
    AnIntConfig(an_int=0)
    AnIntConfig(an_int=-5)
    with pytest.raises(ValidationError, match=" a multiple of 5"):
        AnIntConfig(an_int=4)
    with pytest.raises(ValidationError, match=" a multiple of 5"):
        AnIntConfig(an_int=-4)


def test_float_gtlt() -> None:
    class AnFloatConfig(Config):
        a_float: float = Field(gt=0, lt=10)

    AnFloatConfig(a_float=5)
    with pytest.raises(ValidationError, match=" less than 10"):
        AnFloatConfig(a_float=10)
    with pytest.raises(ValidationError, match=" greater than 0"):
        AnFloatConfig(a_float=0)


def test_float_gele() -> None:
    class AnFloatConfig(Config):
        a_float: float = Field(ge=0, le=10)

    AnFloatConfig(a_float=5)
    AnFloatConfig(a_float=10)
    AnFloatConfig(a_float=0)
    with pytest.raises(ValidationError, match=" less than or equal to 10"):
        AnFloatConfig(a_float=11)
    with pytest.raises(ValidationError, match=" greater than or equal to 0"):
        AnFloatConfig(a_float=-1)


def test_float_multiple() -> None:
    class AnFloatConfig(Config):
        a_float: float = Field(multiple_of=0.5)

    AnFloatConfig(a_float=1)
    AnFloatConfig(a_float=0.5)
    AnFloatConfig(a_float=0)
    with pytest.raises(ValidationError, match=" a multiple of 0.5"):
        AnFloatConfig(a_float=0.25)
    with pytest.raises(ValidationError, match=" a multiple of 0.5"):
        AnFloatConfig(a_float=-0.3)


def test_list_length() -> None:
    class AListConfig(Config):
        a_list: List[int] = Field(min_items=2, max_items=10)

    AListConfig(a_list=[1, 2])
    with pytest.raises(ValidationError, match=" at least 2 items"):
        AListConfig(a_list=[1])
    with pytest.raises(ValidationError, match=" at most 10 items"):
        AListConfig(a_list=[1] * 11)


@pytest.mark.skip("removed in pydantic 2")
def test_list_uniqueness() -> None:
    class AListConfig(Config):
        a_list: List[int] = Field(unique_items=True)

    AListConfig(a_list=[1, 2])
    with pytest.raises(ValidationError, match="the list has duplicated items"):
        AListConfig(a_list=[1, 1])
    with pytest.raises(ValidationError, match="the list has duplicated items"):
        AListConfig(a_list=[1, 2, 1])


def test_with_constr() -> None:
    # Pydantic does not like it when you use constr(), but this just sanity checks that
    # we can use it in place of a field
    class AStringConfig(Config):
        a_str: constr(min_length=2, max_length=10)  # type: ignore

    AStringConfig(a_str="foo")
    with pytest.raises(ValidationError, match=" at least 2 characters"):
        AStringConfig(a_str="f")
    with pytest.raises(ValidationError, match=" at most 10 characters"):
        AStringConfig(a_str="foofoofoofoofoo")


def test_with_conlist() -> None:
    try:

        class AListConfig(Config):  # type: ignore
            a_list: conlist(int, min_length=2, max_length=10)  # type: ignore

    except:

        class AListConfig(Config):
            a_list: conlist(int, min_items=2, max_items=10)  # type: ignore

    AListConfig(a_list=[1, 2])
    with pytest.raises(ValidationError, match=" at least 2 items"):
        AListConfig(a_list=[1])
    with pytest.raises(ValidationError, match=" at most 10 items"):
        AListConfig(a_list=[1] * 11)
