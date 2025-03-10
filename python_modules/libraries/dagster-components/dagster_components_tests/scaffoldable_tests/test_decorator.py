import pytest
from dagster._check.functions import CheckError
from dagster_components.blueprint import Blueprint, blueprint, get_blueprint, has_blueprint


# Example usage:
def test_basic_usage() -> None:
    # Example blueprint class
    class MyBlueprint(Blueprint):
        pass

    # Example decorated class
    @blueprint(MyBlueprint)
    class MyClass:
        pass

    # Example undecorated class
    class RegularClass:
        pass

    # Test the functions
    assert has_blueprint(MyClass) is True
    assert has_blueprint(RegularClass) is False
    assert isinstance(get_blueprint(MyClass), MyBlueprint)
    with pytest.raises(CheckError):
        get_blueprint(RegularClass)


def test_inheritance() -> None:
    class ScaffolderOne(Blueprint): ...

    class ScaffolderTwo(Blueprint): ...

    @blueprint(ScaffolderOne)
    class ClassOne: ...

    @blueprint(ScaffolderTwo)
    class ClassTwo(ClassOne): ...

    assert has_blueprint(ClassOne) is True
    assert isinstance(get_blueprint(ClassOne), ScaffolderOne)

    assert has_blueprint(ClassTwo) is True
    assert isinstance(get_blueprint(ClassTwo), ScaffolderTwo)
