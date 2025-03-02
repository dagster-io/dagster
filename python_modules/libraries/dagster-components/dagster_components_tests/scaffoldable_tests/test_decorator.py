import pytest
from dagster._check.functions import CheckError
from dagster_components.scaffoldable.decorator import (
    Scaffoldable,
    get_scaffolder,
    is_scaffoldable_class,
    scaffoldable,
)


# Example usage:
def test_basic_usage() -> None:
    # Example scaffolder class
    class MyScaffolder(Scaffoldable):
        pass

    # Example decorated class
    @scaffoldable(MyScaffolder)
    class MyClass:
        pass

    # Example undecorated class
    class RegularClass:
        pass

    # Test the functions
    assert is_scaffoldable_class(MyClass) is True
    assert is_scaffoldable_class(RegularClass) is False
    assert get_scaffolder(MyClass) is MyScaffolder
    with pytest.raises(CheckError):
        get_scaffolder(RegularClass)
