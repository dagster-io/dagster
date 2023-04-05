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
        match="""Error defining Dagster config class <class 'test_errors.test_invalid_config_type_basic.<locals>.DoSomethingConfig'> on field 'unsupported_param'.
Unable to resolve config type <class 'test_errors.test_invalid_config_type_basic.<locals>.MyUnsupportedType'>.


This value can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type""",
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
        match="""Error defining Dagster config class <class 'test_errors.test_invalid_config_type_nested.<locals>.MyNestedConfig'> on field 'unsupported_param'.
Unable to resolve config type <class 'test_errors.test_invalid_config_type_nested.<locals>.MyUnsupportedType'>.


This value can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type""",
    ):

        @op
        def my_op(config: DoSomethingConfig):
            pass


def test_invalid_resource_basic() -> None:
    class MyUnsupportedType:
        pass

    class MyBadResource(ConfigurableResource):
        unsupported_param: MyUnsupportedType

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match="""Error defining Dagster config class <class 'test_errors.test_invalid_resource_basic.<locals>.MyBadResource'> on field 'unsupported_param'.
Unable to resolve config type <class 'test_errors.test_invalid_resource_basic.<locals>.MyUnsupportedType'>.


This value can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type


If this value represents a resource dependency, its annotation must either:
    - Extend dagster.ConfigurableResource, dagster.ConfigurableIOManager, or
    - Be wrapped in a ResourceDependency annotation, e.g. ResourceDependency\\[GitHub\\]""",
    ):
        MyBadResource(unsupported_param=MyUnsupportedType())
