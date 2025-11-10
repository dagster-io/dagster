import enum
from collections.abc import Mapping
from typing import Any, Literal, Optional, TypeAlias, Union

import dagster as dg
import pydantic
import pytest
from dagster import Field as LegacyDagsterField
from dagster._config.config_type import ConfigTypeKind
from dagster._config.pythonic_config.config import PermissiveConfig
from dagster._config.type_printer import print_config_type_to_string
from dagster._utils.cached_method import cached_method


def test_default_config_class_non_permissive() -> None:
    class AnOpConfig(dg.Config):
        a_string: str
        an_int: int

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    @dg.job
    def a_job():
        a_struct_config_op()

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {"a_string": "foo", "an_int": 2, "a_bool": True}
                    }
                }
            }
        )


def test_struct_config_permissive() -> None:
    class AnOpConfig(dg.PermissiveConfig):
        a_string: str
        an_int: int

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

        # Can pull out config dict to access permissive fields
        assert config.dict() == {"a_string": "foo", "an_int": 2, "a_bool": True}
        assert config._convert_to_config_dictionary() == {  # noqa: SLF001
            "a_string": "foo",
            "an_int": 2,
            "a_bool": True,
        }

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_struct_config_op.config_schema.config_type
    assert a_struct_config_op.config_schema.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE
    assert list(a_struct_config_op.config_schema.config_type.fields.keys()) == [  # type: ignore
        "a_string",
        "an_int",
    ]

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {"config": {"a_string": "foo", "an_int": 2, "a_bool": True}}
            }
        }
    )

    assert executed["yes"]


def test_struct_config_persmissive_cached_method() -> None:
    calls = {"plus": 0}

    class PlusConfig(dg.PermissiveConfig):
        x: int
        y: int

        @cached_method
        def plus(self):
            calls["plus"] += 1
            return self.x + self.y

    plus_config = PlusConfig(x=1, y=2, z=10)  # type: ignore

    assert plus_config.plus() == 3
    assert calls["plus"] == 1

    assert plus_config.plus() == 3
    assert calls["plus"] == 1


def test_struct_config_array() -> None:
    class AnOpConfig(dg.Config):
        a_string_list: list[str]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string_list == ["foo", "bar"]

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string_list": ["foo", "bar"]}}}}
    )
    assert executed["yes"]

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"a_string_list": ["foo", "bar", 3]}}}}
        )


def test_struct_config_map() -> None:
    class AnOpConfig(dg.Config):
        a_string_to_int_dict: dict[str, int]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string_to_int_dict == {"foo": 1, "bar": 2}

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string_to_int_dict": {"foo": 1, "bar": 2}}}}}
    )
    assert executed["yes"]

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {"a_string_to_int_dict": {"foo": 1, "bar": 2, "baz": "qux"}}
                    }
                }
            }
        )

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"a_string_to_int_dict": {"foo": 1, 2: 4}}}}}
        )


def test_struct_config_mapping() -> None:
    class AnOpConfig(dg.Config):
        a_string_to_int_mapping: Mapping[str, int]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string_to_int_mapping == {"foo": 1, "bar": 2}

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {"config": {"a_string_to_int_mapping": {"foo": 1, "bar": 2}}}
            }
        }
    )
    assert executed["yes"]


def test_struct_config_mapping_list() -> None:
    class AnOpConfig(dg.Config):
        a_list_of_string_to_int_mapping: list[Mapping[str, int]]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_list_of_string_to_int_mapping == [{"foo": 1, "bar": 2}]

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {"a_list_of_string_to_int_mapping": [{"foo": 1, "bar": 2}]}
                }
            }
        }
    )
    assert executed["yes"]


def test_complex_config_schema() -> None:
    class AnOpConfig(dg.Config):
        a_complex_thing: Mapping[int, list[Mapping[str, Optional[int]]]]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_complex_thing == {5: [{"foo": 1, "bar": 2, "baz": None}]}

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {"a_complex_thing": {5: [{"foo": 1, "bar": 2, "baz": None}]}}
                }
            }
        }
    )
    assert executed["yes"]

    a_struct_config_op(AnOpConfig(a_complex_thing={5: [{"foo": 1, "bar": 2, "baz": None}]}))  # type: ignore
    a_struct_config_op(config=AnOpConfig(a_complex_thing={5: [{"foo": 1, "bar": 2, "baz": None}]}))  # type: ignore
    a_struct_config_op({"a_complex_thing": {5: [{"foo": 1, "bar": 2, "baz": None}]}})
    a_struct_config_op(config={"a_complex_thing": {5: [{"foo": 1, "bar": 2, "baz": None}]}})


@pytest.mark.skip(reason="not yet supported")
def test_struct_config_optional_nested() -> None:
    class ANestedConfig(dg.Config):
        a_str: str

    class AnOpConfig(dg.Config):
        an_optional_nested: Optional[ANestedConfig]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.an_optional_nested is None

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {}}}})
    assert executed["yes"]

    a_struct_config_op(AnOpConfig(an_optional_nested=None))
    a_struct_config_op(config=AnOpConfig(an_optional_nested=None))


def test_struct_config_nested_in_list() -> None:
    class ANestedConfig(dg.Config):
        a_str: str

    class AnOpConfig(dg.Config):
        an_optional_nested: list[ANestedConfig]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.an_optional_nested[0].a_str == "foo"
        assert config.an_optional_nested[1].a_str == "bar"

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {"an_optional_nested": [{"a_str": "foo"}, {"a_str": "bar"}]}
                }
            }
        }
    )
    assert executed["yes"]


def test_struct_config_optional_nested_in_list() -> None:
    class ANestedConfig(dg.Config):
        a_str: str

    class AnOpConfig(dg.Config):
        an_optional_nested: Optional[list[ANestedConfig]]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True

        assert not config.an_optional_nested or config.an_optional_nested[0].a_str == "foo"
        assert not config.an_optional_nested or config.an_optional_nested[1].a_str == "bar"

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {"an_optional_nested": [{"a_str": "foo"}, {"a_str": "bar"}]}
                }
            }
        }
    ).success
    assert executed["yes"]
    executed.clear()

    assert a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {}}}}).success
    assert executed["yes"]
    executed.clear()

    assert a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"an_optional_nested": None}}}}
    ).success
    assert executed["yes"]


def test_struct_config_nested_in_dict() -> None:
    class ANestedConfig(dg.Config):
        a_str: str

    class AnOpConfig(dg.Config):
        an_optional_nested: dict[str, ANestedConfig]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.an_optional_nested["foo"].a_str == "foo"
        assert config.an_optional_nested["bar"].a_str == "bar"

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {
                        "an_optional_nested": {"foo": {"a_str": "foo"}, "bar": {"a_str": "bar"}}
                    }
                }
            }
        }
    )
    assert executed["yes"]


@pytest.mark.parametrize(
    "key_type, keys",
    [(str, ["foo", "bar"]), (int, [1, 2]), (float, [1.0, 2.0]), (bool, [True, False])],
)
def test_struct_config_map_different_key_type(key_type: type, keys: list[Any]):
    class AnOpConfig(dg.Config):
        my_dict: dict[key_type, int]  # type: ignore # ignored for update, fix me!

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.my_dict == {keys[0]: 1, keys[1]: 2}

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"my_dict": {keys[0]: 1, keys[1]: 2}}}}}
    )
    assert executed["yes"]


def test_discriminated_unions() -> None:
    class Cat(dg.Config):
        pet_type: Literal["cat"]
        meows: int

    class Dog(dg.Config):
        pet_type: Literal["dog"]
        barks: float

    class Lizard(dg.Config):
        pet_type: Literal["reptile", "lizard"]
        scales: bool

    class OpConfigWithUnion(dg.Config):
        pet: Union[Cat, Dog, Lizard] = pydantic.Field(..., discriminator="pet_type")
        n: int

    executed = {}

    @dg.op
    def a_struct_config_op(config: OpConfigWithUnion):
        if config.pet.pet_type == "cat":
            assert config.pet.meows == 2
        elif config.pet.pet_type == "dog":
            assert config.pet.barks == 3.0
        elif config.pet.pet_type == "lizard":
            assert config.pet.scales
        assert config.n == 4

        executed["yes"] = True

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"pet": {"cat": {"meows": 2}}, "n": 4}}}}
    )
    assert executed["yes"]

    executed = {}
    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"pet": {"dog": {"barks": 3.0}}, "n": 4}}}}
    )
    assert executed["yes"]

    executed = {}
    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"pet": {"lizard": {"scales": True}}, "n": 4}}}}
    )
    assert executed["yes"]

    executed = {}
    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"pet": {"reptile": {"scales": True}}, "n": 4}}}}
    )
    assert executed["yes"]

    # Ensure passing value which doesn't exist errors
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"pet": {"octopus": {"meows": 2}}, "n": 4}}}}
        )

    # Disallow passing multiple discriminated union values
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {
                            "pet": {"reptile": {"scales": True}, "dog": {"barks": 3.0}},
                            "n": 4,
                        }
                    }
                }
            }
        )


def test_nested_discriminated_unions() -> None:
    class Poodle(dg.Config):
        breed_type: Literal["poodle"]
        fluffy: bool

    class Dachshund(dg.Config):
        breed_type: Literal["dachshund"]
        long: bool

    class Cat(dg.Config):
        pet_type: Literal["cat"]
        meows: int

    class Dog(dg.Config):
        pet_type: Literal["dog"]
        barks: float
        breed: Union[Poodle, Dachshund] = pydantic.Field(..., discriminator="breed_type")

    class OpConfigWithUnion(dg.Config):
        pet: Union[Cat, Dog] = pydantic.Field(..., discriminator="pet_type")
        n: int

    executed = {}

    @dg.op
    def a_struct_config_op(config: OpConfigWithUnion):
        assert config.pet.pet_type == "dog"
        assert isinstance(config.pet, Dog)
        assert config.pet.breed.breed_type == "poodle"
        assert isinstance(config.pet.breed, Poodle)
        assert config.pet.breed.fluffy

        executed["yes"] = True

    @dg.job
    def a_job():
        a_struct_config_op()

    assert a_job

    a_job.execute_in_process(
        {
            "ops": {
                "a_struct_config_op": {
                    "config": {
                        "pet": {"dog": {"barks": 3.0, "breed": {"poodle": {"fluffy": True}}}},
                        "n": 4,
                    }
                }
            }
        }
    )
    assert executed["yes"]


def test_discriminated_unions_direct_instantiation() -> None:
    class Cat(dg.Config):
        pet_type: Literal["cat"] = "cat"
        meows: int

    class Dog(dg.Config):
        pet_type: Literal["dog"] = "dog"
        barks: float

    class Lizard(dg.Config):
        pet_type: Literal["reptile", "lizard"] = "reptile"
        scales: bool

    class OpConfigWithUnion(dg.Config):
        pet: Union[Cat, Dog, Lizard] = pydantic.Field(..., discriminator="pet_type")
        n: int

    config = OpConfigWithUnion(pet=Cat(meows=3), n=5)
    assert isinstance(config.pet, Cat)
    assert config.pet.meows == 3


def test_nested_discriminated_config_instantiation() -> None:
    class Poodle(dg.Config):
        breed_type: Literal["poodle"] = "poodle"
        fluffy: bool

    class Dachshund(dg.Config):
        breed_type: Literal["dachshund"] = "dachshund"
        long: bool

    class Cat(dg.Config):
        pet_type: Literal["cat"] = "cat"
        meows: int

    class Dog(dg.Config):
        pet_type: Literal["dog"] = "dog"
        barks: float
        breed: Union[Poodle, Dachshund] = pydantic.Field(..., discriminator="breed_type")

    class OpConfigWithUnion(dg.Config):
        pet: Union[Cat, Dog] = pydantic.Field(..., discriminator="pet_type")
        n: int

    config = OpConfigWithUnion(pet=Dog(barks=5.5, breed=Poodle(fluffy=True)), n=3)
    assert isinstance(config.pet, Dog)
    assert config.pet.barks == 5.5
    assert config.pet.pet_type == "dog"
    assert isinstance(config.pet.breed, Poodle)
    assert config.pet.breed.fluffy
    assert config.pet.breed.breed_type == "poodle"


def test_nested_discriminated_resource_instantiation() -> None:
    class Poodle(dg.Config):
        breed_type: Literal["poodle"] = "poodle"
        fluffy: bool

    class Dachshund(dg.Config):
        breed_type: Literal["dachshund"] = "dachshund"
        long: bool

    class Cat(dg.Config):
        pet_type: Literal["cat"] = "cat"
        meows: int

    class Dog(dg.Config):
        pet_type: Literal["dog"] = "dog"
        barks: float
        breed: Union[Poodle, Dachshund] = pydantic.Field(..., discriminator="breed_type")

    class ResourceWithUnion(dg.ConfigurableResource):
        pet: Union[Cat, Dog] = pydantic.Field(..., discriminator="pet_type")
        n: int

    resource_with_union = ResourceWithUnion(pet=Dog(barks=5.5, breed=Poodle(fluffy=True)), n=3)
    assert isinstance(resource_with_union.pet, Dog)
    assert resource_with_union.pet.barks == 5.5
    assert resource_with_union.pet.pet_type == "dog"
    assert isinstance(resource_with_union.pet.breed, Poodle)
    assert resource_with_union.pet.breed.fluffy
    assert resource_with_union.pet.breed.breed_type == "poodle"

    executed = {}

    @dg.asset
    def my_asset_uses_resource(resource_with_union: ResourceWithUnion):
        assert isinstance(resource_with_union.pet, Dog)
        assert resource_with_union.pet.barks == 5.5
        assert resource_with_union.pet.pet_type == "dog"
        assert isinstance(resource_with_union.pet.breed, Poodle)
        assert resource_with_union.pet.breed.fluffy
        assert resource_with_union.pet.breed.breed_type == "poodle"
        executed["yes"] = True

    defs = dg.Definitions(
        assets=[my_asset_uses_resource],
        resources={"resource_with_union": resource_with_union},
    )
    assert defs.resolve_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]


def test_struct_config_optional_map() -> None:
    class AnOpConfig(dg.Config):
        an_optional_dict: Optional[dict[str, int]]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True

    assert print_config_type_to_string(
        a_struct_config_op.config_schema.config_type
    ) == print_config_type_to_string(
        dg.Shape(
            fields={"an_optional_dict": LegacyDagsterField(dg.Noneable(dg.Map(str, dg.IntSource)))}
        )
    )

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"an_optional_dict": {"foo": 1, "bar": 2}}}}}
    )
    assert executed["yes"]
    executed.clear()

    a_job.execute_in_process()
    assert executed["yes"]
    executed.clear()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"an_optional_dict": None}}}}
    )
    assert executed["yes"]

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {"an_optional_dict": {"foo": 1, "bar": 2, "baz": "qux"}}
                    }
                }
            }
        )


def test_struct_config_optional_array() -> None:
    class AnOpConfig(dg.Config):
        a_string_list: Optional[list[str]]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string_list": ["foo", "bar"]}}}}
    )
    assert executed["yes"]
    executed.clear()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"a_string_list": None}}}})
    assert executed["yes"]
    executed.clear()

    a_job.execute_in_process()
    assert executed["yes"]

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"a_string_list": ["foo", "bar", 3]}}}}
        )


def test_str_enum_value() -> None:
    class MyEnum(enum.Enum):
        FOO = "foo"
        BAR = "bar"

    class AnOpConfig(dg.Config):
        an_enum: MyEnum

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        assert config.an_enum == MyEnum.FOO
        executed["yes"] = True

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"an_enum": "FOO"}}}})
    assert executed["yes"]

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"an_enum": "BAZ"}}}})

    # must pass enum name, not value
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"an_enum": "foo"}}}})


def test_literal_in_op_config() -> None:
    class AnOpConfig(dg.Config):
        a_literal: Literal["foo", "bar"] = "foo"

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        assert isinstance(config.a_literal, str)
        assert config.a_literal in ["foo", "bar"]

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"a_literal": "bar"}}}})

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {"a_literal": "baz"}}}})


def test_literal_in_resource_config() -> None:
    class MyResource(dg.ConfigurableResource):
        a_literal: Literal["foo", "bar"] = "foo"

        def setup_for_execution(self, context):
            assert self.a_literal in ["foo", "bar"]

    @dg.op
    def my_op(my_resource: MyResource):
        pass

    @dg.job
    def a_job():
        my_op()

    a_job.execute_in_process(resources={"my_resource": MyResource()})

    a_job.execute_in_process(resources={"my_resource": MyResource(a_literal="bar")})

    with pytest.raises(pydantic.ValidationError):
        a_job.execute_in_process(resources={"my_resource": MyResource(a_literal="baz")})  # type: ignore


def test_enum_complex() -> None:
    class MyEnum(enum.Enum):
        FOO = "foo"
        BAR = "bar"

    class AnOpConfig(dg.Config):
        an_optional_enum: Optional[MyEnum]
        an_enum_list: list[MyEnum]

    executed = {}

    @dg.op
    def a_struct_config_op(config: AnOpConfig):
        assert config.an_optional_enum is None
        assert config.an_enum_list == [MyEnum.FOO, MyEnum.BAR]
        executed["yes"] = True

    @dg.job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"an_enum_list": ["FOO", "BAR"]}}}}
    )
    assert executed["yes"]

    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"an_enum_list": ["FOO", "BAZ"]}}}}
        )


def test_struct_config_non_optional_none_input_errors() -> None:
    executed = {}

    class AnOpListConfig(dg.Config):
        a_string_list: list[str]

    @dg.op
    def a_list_op(config: AnOpListConfig):
        executed["yes"] = True

    class AnOpMapConfig(dg.Config):
        a_string_list: dict[str, str]

    @dg.op
    def a_map_op(config: AnOpMapConfig):
        executed["yes"] = True

    @dg.job
    def a_job():
        a_map_op()
        a_list_op()

    a_job.execute_in_process(
        {
            "ops": {
                "a_map_op": {"config": {"a_string_list": {"foo": "bar"}}},
                "a_list_op": {"config": {"a_string_list": ["foo", "bar"]}},
            }
        }
    )
    assert executed["yes"]
    executed.clear()

    # Validate that we error when we pass None to a non-optional field
    # or when we omit the field entirely
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_map_op": {"config": {"a_string_list": None}},
                    "a_list_op": {"config": {"a_string_list": ["foo", "bar"]}},
                }
            }
        )
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_list_op": {"config": {"a_string_list": ["foo", "bar"]}},
                }
            }
        )
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_map_op": {"config": {"a_string_list": {"foo": "bar"}}},
                    "a_list_op": {"config": {"a_string_list": None}},
                }
            }
        )
    with pytest.raises(dg.DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_map_op": {"config": {"a_string_list": {"foo": "bar"}}},
                }
            }
        )


FooBarLiteral: TypeAlias = Literal["foo", "bar"]


def test_conversion_to_fields() -> None:
    class ConfigClassToConvert(dg.Config):
        a_string: str
        an_int: str
        with_description: str = pydantic.Field(description="a description")
        with_default_value: int = pydantic.Field(default=12)
        optional_str: Optional[str] = None
        a_literal: FooBarLiteral
        a_default_literal: FooBarLiteral = "bar"
        a_literal_with_description: FooBarLiteral = pydantic.Field(
            default="foo", description="a description"
        )

    fields = ConfigClassToConvert.to_fields_dict()

    assert isinstance(fields, dict)
    assert set(fields.keys()) == {
        "a_string",
        "an_int",
        "with_description",
        "with_default_value",
        "optional_str",
        "a_literal",
        "a_default_literal",
        "a_literal_with_description",
    }
    assert fields["with_description"].description == "a description"
    assert fields["with_description"].is_required is True
    assert fields["with_default_value"].default_value == 12
    assert not fields["with_default_value"].is_required
    assert fields["optional_str"]
    assert fields["optional_str"].is_required is False
    assert fields["a_literal"].is_required is True
    assert fields["a_default_literal"].is_required is False
    assert fields["a_default_literal"].default_value == "bar"
    assert fields["a_literal_with_description"].description == "a description"


def test_to_config_dict_combined_with_cached_method() -> None:
    class ConfigWithCachedMethod(dg.Config):
        a_string: str

        @cached_method
        def a_string_cached(self) -> str:
            return "foo"

    obj = ConfigWithCachedMethod(a_string="bar")
    obj.a_string_cached()
    assert obj._convert_to_config_dictionary() == {"a_string": "bar"}  # noqa: SLF001


def test_aliases() -> None:
    class ConfigWithAlias(dg.ConfigurableResource):
        field_name: Optional[Mapping[str, str]] = pydantic.Field(
            alias="alias_name",
            default=None,
        )

    @dg.op
    def echo_config(my_resource: ConfigWithAlias):
        return my_resource.field_name

    @dg.job
    def echo_job():
        echo_config()

    result = echo_job.execute_in_process(resources={"my_resource": ConfigWithAlias()})
    assert result.success
    assert result.output_for_node("echo_config") is None

    d = {"test": "test"}
    result = echo_job.execute_in_process(resources={"my_resource": ConfigWithAlias(alias_name=d)})
    assert result.output_for_node("echo_config") == d


def test_permissive_extra_field_via_dot():
    class ExtraConfig(PermissiveConfig):
        foo: int

    conf = ExtraConfig(foo=10, bar="hello", baz=[1, 2, 3])  # type: ignore
    conf1 = ExtraConfig(foo=10, bar="hello", baz=[1, 2, 3])  # type: ignore
    assert conf == conf1
    assert conf.foo == 10
    assert conf.bar == "hello"
    assert conf.baz == [1, 2, 3]
    # confirm it's in dict and convert_to_config_dictionary
    expected = {"foo": 10, "bar": "hello", "baz": [1, 2, 3]}
    assert conf.model_dump() == expected
