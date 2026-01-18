from enum import Enum

import dagster as dg


def test_enum_name_config():
    class MyEnum(str, Enum):
        TYPE_A = "a"
        TYPE_B = "b"

    class MyConfig(dg.Config):
        enum: MyEnum = MyEnum.TYPE_A

    @dg.asset
    def my_asset(
        config: MyConfig,
    ):
        return config.enum.value

    dg.materialize([my_asset])


def test_enum_name_resource_x():
    class MyEnum(str, Enum):
        TYPE_A = "a"
        TYPE_B = "b"

    class MyResource(dg.ConfigurableResource):
        enum: MyEnum = MyEnum.TYPE_A

    @dg.asset
    def my_asset(my_resource: MyResource):
        return my_resource.enum.value

    dg.materialize([my_asset], resources={"my_resource": MyResource()})


def test_enum_name_resource_override_name():
    class MyEnum(str, Enum):
        TYPE_A = "a"
        TYPE_B = "b"

    class MyResource(dg.ConfigurableResource):
        enum: MyEnum = MyEnum.TYPE_A

    @dg.asset
    def my_asset(my_resource: MyResource):
        return my_resource.enum.value

    dg.materialize([my_asset], resources={"my_resource": MyResource(enum=MyEnum.TYPE_A.name)})  # pyright: ignore[reportArgumentType]


def test_enum_name_resource_override_enum():
    class MyEnum(str, Enum):
        TYPE_A = "a"
        TYPE_B = "b"

    class MyResource(dg.ConfigurableResource):
        enum: MyEnum = MyEnum.TYPE_A

    @dg.asset
    def my_asset(my_resource: MyResource):
        return my_resource.enum.value

    dg.materialize([my_asset], resources={"my_resource": MyResource(enum=MyEnum.TYPE_A)})
