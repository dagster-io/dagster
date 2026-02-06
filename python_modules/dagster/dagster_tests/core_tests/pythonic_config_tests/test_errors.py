# ruff: noqa: UP006
import warnings
from typing import Tuple  # noqa: UP035

import dagster as dg
import pytest
from dagster import Field as LegacyDagsterField
from dagster._config.pythonic_config import ConfigurableResourceFactory
from dagster._core.errors import (
    DagsterInvalidDagsterTypeInPythonicConfigDefinitionError,
    DagsterInvalidPythonicConfigDefinitionError,
)


def test_invalid_config_type_basic() -> None:
    class MyUnsupportedType:
        pass

    class DoSomethingConfig(dg.Config):
        unsupported_param: MyUnsupportedType

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class <class 'test_errors.test_invalid_config_type_basic.<locals>.DoSomethingConfig'> on field 'unsupported_param'.
Unable to resolve config type <class 'test_errors.test_invalid_config_type_basic.<locals>.MyUnsupportedType'> to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)""",
    ):

        @dg.op
        def my_op(config: DoSomethingConfig):
            pass


def test_invalid_config_type_nested() -> None:
    class MyUnsupportedType:
        pass

    class MyNestedConfig(dg.Config):
        unsupported_param: MyUnsupportedType

    class DoSomethingConfig(dg.Config):
        nested_param: MyNestedConfig

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class <class 'test_errors.test_invalid_config_type_nested.<locals>.MyNestedConfig'> on field 'unsupported_param'.
Unable to resolve config type <class 'test_errors.test_invalid_config_type_nested.<locals>.MyUnsupportedType'> to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)""",
    ):

        @dg.op
        def my_op(config: DoSomethingConfig):
            pass


def test_invalid_resource_basic() -> None:
    class MyUnsupportedType:
        pass

    class MyBadResource(dg.ConfigurableResource):
        unsupported_param: MyUnsupportedType

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class <class 'test_errors.test_invalid_resource_basic.<locals>.MyBadResource'> on field 'unsupported_param'.
Unable to resolve config type <class 'test_errors.test_invalid_resource_basic.<locals>.MyUnsupportedType'> to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)


If this config type represents a resource dependency, its annotation must either:
    - Extend dagster.ConfigurableResource, dagster.ConfigurableIOManager, or
    - Be wrapped in a ResourceDependency annotation, e.g. ResourceDependency\[MyUnsupportedType\]""",
    ):
        MyBadResource(unsupported_param=MyUnsupportedType())


def test_invalid_config_class_directly_on_op() -> None:
    class MyUnsupportedType:
        pass

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class.
Unable to resolve config type <class 'test_errors.test_invalid_config_class_directly_on_op.<locals>.MyUnsupportedType'> to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)""",
    ):

        @dg.op
        def my_op(config: MyUnsupportedType):
            pass

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class.
Unable to resolve config type <class 'test_errors.test_invalid_config_class_directly_on_op.<locals>.MyUnsupportedType'> to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)""",
    ):

        @dg.asset
        def my_asset(config: MyUnsupportedType):
            pass


def test_unsupported_primitive_config_type_directly_on_op() -> None:
    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class.
Unable to resolve config type typing.Tuple\[str, str\] to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)""",
    ):

        @dg.op
        def my_op(config: Tuple[str, str]):
            pass

    with pytest.raises(
        DagsterInvalidPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class.
Unable to resolve config type typing.Tuple\[str, str\] to a supported Dagster config type.


This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type \(https://docs.pydantic.dev/usage/types/#discriminated-unions-aka-tagged-unions\)""",
    ):

        @dg.asset
        def my_asset(config: Tuple[str, str]):
            pass


def test_annotate_with_resource_factory() -> None:
    class MyStringFactory(ConfigurableResourceFactory[str]):
        def create_resource(self, context: None) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
            return "hello"

    # https://github.com/dagster-io/dagster/issues/18017
    target = "an unknown"  # should be "a '<class 'str'>'"
    ttype = "Any"  # should be "str"

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource param 'my_string' is annotated as '<class"
            " 'test_errors.test_annotate_with_resource_factory.<locals>.MyStringFactory'>', but"
            " '<class 'test_errors.test_annotate_with_resource_factory.<locals>.MyStringFactory'>'"
            f" outputs {target} value to user code such as @ops and @assets. This"
            f" annotation should instead be 'ResourceParam\\[{ttype}\\]'"
        ),
    ):

        @dg.op
        def my_op(my_string: MyStringFactory):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource param 'my_string' is annotated as '<class"
            " 'test_errors.test_annotate_with_resource_factory.<locals>.MyStringFactory'>', but"
            " '<class 'test_errors.test_annotate_with_resource_factory.<locals>.MyStringFactory'>'"
            f" outputs {target} value to user code such as @ops and @assets. This"
            f" annotation should instead be 'ResourceParam\\[{ttype}\\]'"
        ),
    ):

        @dg.asset
        def my_asset(my_string: MyStringFactory):
            pass

    class MyUnspecifiedFactory(ConfigurableResourceFactory):
        def create_resource(self, context: None) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
            return "hello"

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Resource param 'my_string' is annotated as '<class"
            " 'test_errors.test_annotate_with_resource_factory.<locals>.MyUnspecifiedFactory'>',"
            " but '<class"
            " 'test_errors.test_annotate_with_resource_factory.<locals>.MyUnspecifiedFactory'>'"
            " outputs an unknown value to user code such as @ops and @assets. This annotation"
            " should instead be 'ResourceParam\\[Any\\]' or 'ResourceParam\\[<output type>\\]'"
        ),
    ):

        @dg.op
        def my_op2(my_string: MyUnspecifiedFactory):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Resource param 'my_string' is annotated as '<class"
            " 'test_errors.test_annotate_with_resource_factory.<locals>.MyUnspecifiedFactory'>',"
            " but '<class"
            " 'test_errors.test_annotate_with_resource_factory.<locals>.MyUnspecifiedFactory'>'"
            " outputs an unknown value to user code such as @ops and @assets. This annotation"
            " should instead be 'ResourceParam\\[Any\\]' or 'ResourceParam\\[<output type>\\]'"
        ),
    ):

        @dg.asset
        def my_asset2(my_string: MyUnspecifiedFactory):
            pass


def test_annotate_with_resource_factory_schedule_sensor() -> None:
    class MyStringFactory(ConfigurableResourceFactory[str]):
        def create_resource(self, context: None) -> str:  # pyright: ignore[reportIncompatibleMethodOverride]
            return "hello"

    # https://github.com/dagster-io/dagster/issues/18017
    target = "an unknown"  # should be "a '<class 'str'>'"
    ttype = "Any"  # should be "str"

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource param 'my_string' is annotated as '<class"
            " 'test_errors.test_annotate_with_resource_factory_schedule_sensor.<locals>.MyStringFactory'>',"
            " but '<class"
            " 'test_errors.test_annotate_with_resource_factory_schedule_sensor.<locals>.MyStringFactory'>'"
            f" outputs {target} value to user code such as @ops and @assets. This"
            f" annotation should instead be 'ResourceParam\\[{ttype}\\]'"
        ),
    ):

        @dg.sensor(job_name="foo")
        def my_sensor(my_string: MyStringFactory):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "Resource param 'my_string' is annotated as '<class"
            " 'test_errors.test_annotate_with_resource_factory_schedule_sensor.<locals>.MyStringFactory'>',"
            " but '<class"
            " 'test_errors.test_annotate_with_resource_factory_schedule_sensor.<locals>.MyStringFactory'>'"
            f" outputs {target} value to user code such as @ops and @assets. This"
            f" annotation should instead be 'ResourceParam\\[{ttype}\\]'"
        ),
    ):

        @dg.schedule(job_name="foo", cron_schedule="* * * * *")
        def my_schedule(my_string: MyStringFactory):
            pass


def test_annotate_with_bare_resource_def() -> None:
    class MyResourceDef(dg.ResourceDefinition):
        pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Resource param 'my_resource' is annotated as '<class"
            " 'test_errors.test_annotate_with_bare_resource_def.<locals>.MyResourceDef'>', but"
            " '<class 'test_errors.test_annotate_with_bare_resource_def.<locals>.MyResourceDef'>'"
            " outputs an unknown value to user code such as @ops and @assets. This annotation"
            " should instead be 'ResourceParam\\[Any\\]' or 'ResourceParam\\[<output type>\\]'"
        ),
    ):

        @dg.op
        def my_op(my_resource: MyResourceDef):
            pass

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Resource param 'my_resource' is annotated as '<class"
            " 'test_errors.test_annotate_with_bare_resource_def.<locals>.MyResourceDef'>', but"
            " '<class 'test_errors.test_annotate_with_bare_resource_def.<locals>.MyResourceDef'>'"
            " outputs an unknown value to user code such as @ops and @assets. This annotation"
            " should instead be 'ResourceParam\\[Any\\]' or 'ResourceParam\\[<output type>\\]'"
        ),
    ):

        @dg.asset
        def my_asset(my_resource: MyResourceDef):
            pass


def test_using_dagster_field_by_mistake_config() -> None:
    class MyConfig(dg.Config):
        my_str: str = LegacyDagsterField(str, description="This is a string")  # type: ignore

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Using 'dagster.Field' is not supported within a Pythonic config or resource"
            " definition. 'dagster.Field' should only be used in legacy Dagster config schemas. Did"
            " you mean to use 'pydantic.Field' instead?"
        ),
    ):

        @dg.op
        def my_op(config: MyConfig):
            pass


def test_using_dagster_field_by_mistake_resource() -> None:
    class MyResource(dg.ConfigurableResource):
        my_str: str = LegacyDagsterField(str, description="This is a string")  # type: ignore

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Using 'dagster.Field' is not supported within a Pythonic config or resource"
            " definition. 'dagster.Field' should only be used in legacy Dagster config schemas. Did"
            " you mean to use 'pydantic.Field' instead?"
        ),
    ):
        MyResource(my_str="foo")


def test_trying_to_set_a_field() -> None:
    class MyConfig(dg.Config):
        my_str: str

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=r"'MyConfig' is a Pythonic config class and does not support item assignment.",
    ):
        my_config = MyConfig(my_str="foo")
        my_config.my_str = "bar"


def test_trying_to_set_a_field_resource() -> None:
    class MyResource(dg.ConfigurableResource):
        my_str: str

    with pytest.raises(
        dg.DagsterInvalidInvocationError,
        match=(
            r"'MyResource' is a Pythonic resource and does not support item assignment, as it"
            " inherits from 'pydantic.BaseModel' with frozen=True. If trying to"
            " maintain state on this resource, consider building a separate, stateful"
            " client class, and provide a method on the resource to construct and"
            " return the stateful client."
        ),
    ):
        my_resource = MyResource(my_str="foo")
        my_resource.my_str = "bar"


def test_custom_dagster_type_as_config_type() -> None:
    from datetime import datetime

    DagsterDatetime = dg.DagsterType(
        name="DagsterDatetime",
        description="Standard library `datetime.datetime` type as a DagsterType",
        type_check_fn=lambda _, obj: isinstance(obj, datetime),
    )

    with pytest.raises(
        DagsterInvalidDagsterTypeInPythonicConfigDefinitionError,
        match=r"""Error defining Dagster config class 'MyOpConfig' on field 'dagster_type_field'. DagsterTypes cannot be used to annotate a config type. DagsterType is meant only for type checking and coercion in op and asset inputs and outputs.

This config type can be a:
    - Python primitive type
        - int, float, bool, str, list
    - A Python Dict or List type containing other valid types
    - Custom data classes extending dagster.Config
    - A Pydantic discriminated union type""",
    ):

        class MyOpConfig(dg.Config):
            dagster_type_field: DagsterDatetime = datetime(year=2023, month=4, day=30)  # type: ignore


def test_config_named_wrong_thing() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        class DoSomethingConfig(dg.Config):
            a_str: str

        assert len(w) == 0

        @dg.op
        def my_op(config_named_wrong: DoSomethingConfig):
            pass

        assert len(w) == 1
        assert (
            w[0]
            .message.args[0]  # type: ignore
            .startswith(
                "Parameter 'config_named_wrong' on op/asset function 'my_op' was annotated as a dagster.Config type. Did you mean to name this parameter 'config' instead?"
            )
        )

        @dg.asset
        def my_asset(config_named_wrong: DoSomethingConfig):
            pass

        assert len(w) == 2
        assert (
            w[1]
            .message.args[0]  # type: ignore
            .startswith(
                "Parameter 'config_named_wrong' on op/asset function 'my_asset' was annotated as a dagster.Config type. Did you mean to name this parameter 'config' instead?"
            )
        )
