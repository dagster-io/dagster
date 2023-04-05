import pytest
from dagster import Config, op
from dagster._config.structured_config import ConfigurableResource
from dagster._core.errors import DagsterInvalidPythonicConfigDefinitionError


def test_invalid_config_type_basic() -> None:
    class MyUnsupportedType:
        pass

    class DoSomethingConfig(Config):
        unsupported_param: MyUnsupportedType

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=(
            "Error defining Dagster config class <class"
            r" '.*DoSomethingConfig'>on field"
            " 'unsupported_param'.\nUnable to resolve config type <class"
            r" '.*MyUnsupportedType'>."
        ),
    ):

        @op
        def my_op(config: DoSomethingConfig):
            pass


def test_invalid_config_type_nested() -> None:
    class MyUnsupportedType:
        pass

    class MyNestedConfig(Config):
        unsupported_param: MyUnsupportedType

    class DoSomethingConfig(Config):
        nested_param: MyNestedConfig

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=(
            "Error defining Dagster config class <class"
            r" '.*MyNestedConfig'>on field"
            " 'unsupported_param'.\nUnable to resolve config type <class"
            r" '.*MyUnsupportedType'>."
        ),
    ):

        @op
        def my_op(config: DoSomethingConfig):
            pass


def test_invalid_resource_basic() -> None:
    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=(
            "Error defining Dagster config class <class"
            r" '.*MyBadResource'>on field"
            " 'unsupported_param'.\nUnable to resolve config type <class"
            r" '.*MyUnsupportedType'>."
        ),
    ):

        class MyUnsupportedType:
            pass

        class MyBadResource(ConfigurableResource):
            unsupported_param: MyUnsupportedType

        MyBadResource(unsupported_param=MyUnsupportedType())
