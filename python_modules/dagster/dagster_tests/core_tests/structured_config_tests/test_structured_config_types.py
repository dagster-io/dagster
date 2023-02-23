from typing import Any, Dict, List, Mapping, Optional, Type, Union

import pytest
from dagster import job, op
from dagster._config.config_type import ConfigTypeKind
from dagster._config.structured_config import Config, PermissiveConfig
from dagster._core.errors import DagsterInvalidConfigError
from dagster._utils.cached_method import cached_method
from pydantic import Field
from typing_extensions import Literal


def test_default_config_class_non_permissive():
    class AnOpConfig(Config):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

    @job
    def a_job():
        a_struct_config_op()

    with pytest.raises(DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {"a_string": "foo", "an_int": 2, "a_bool": True}
                    }
                }
            }
        )


def test_struct_config_permissive():
    class AnOpConfig(PermissiveConfig):
        a_string: str
        an_int: int

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string == "foo"
        assert config.an_int == 2

        # Can pull out config dict to access permissive fields
        assert config.dict() == {"a_string": "foo", "an_int": 2, "a_bool": True}

    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction

    assert DecoratedOpFunction(a_struct_config_op).has_config_arg()

    # test fields are inferred correctly
    assert a_struct_config_op.config_schema.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE
    assert list(a_struct_config_op.config_schema.config_type.fields.keys()) == [
        "a_string",
        "an_int",
    ]

    @job
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


def test_struct_config_persmissive_cached_method():
    calls = {"plus": 0}

    class PlusConfig(PermissiveConfig):
        x: int
        y: int

        @cached_method
        def plus(self):
            calls["plus"] += 1
            return self.x + self.y

    plus_config = PlusConfig(x=1, y=2)

    assert plus_config.plus() == 3
    assert calls["plus"] == 1

    assert plus_config.plus() == 3
    assert calls["plus"] == 1


def test_struct_config_array():
    class AnOpConfig(Config):
        a_string_list: List[str]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string_list == ["foo", "bar"]

    @job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string_list": ["foo", "bar"]}}}}
    )
    assert executed["yes"]

    with pytest.raises(DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"a_string_list": ["foo", "bar", 3]}}}}
        )


def test_struct_config_map():
    class AnOpConfig(Config):
        a_string_to_int_dict: Dict[str, int]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string_to_int_dict == {"foo": 1, "bar": 2}

    @job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"a_string_to_int_dict": {"foo": 1, "bar": 2}}}}}
    )
    assert executed["yes"]

    with pytest.raises(DagsterInvalidConfigError):
        a_job.execute_in_process(
            {
                "ops": {
                    "a_struct_config_op": {
                        "config": {"a_string_to_int_dict": {"foo": 1, "bar": 2, "baz": "qux"}}
                    }
                }
            }
        )

    with pytest.raises(DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"a_string_to_int_dict": {"foo": 1, 2: 4}}}}}
        )


def test_struct_config_mapping():
    class AnOpConfig(Config):
        a_string_to_int_mapping: Mapping[str, int]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.a_string_to_int_mapping == {"foo": 1, "bar": 2}

    @job
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


@pytest.mark.skip(reason="not yet supported")
def test_struct_config_optional_nested():
    class ANestedConfig(Config):
        a_str: str

    class AnOpConfig(Config):
        an_optional_nested: Optional[ANestedConfig]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.an_optional_nested is None

    @job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process({"ops": {"a_struct_config_op": {"config": {}}}})
    assert executed["yes"]


def test_struct_config_nested_in_list():
    class ANestedConfig(Config):
        a_str: str

    class AnOpConfig(Config):
        an_optional_nested: List[ANestedConfig]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.an_optional_nested[0].a_str == "foo"
        assert config.an_optional_nested[1].a_str == "bar"

    @job
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


def test_struct_config_nested_in_dict():
    class ANestedConfig(Config):
        a_str: str

    class AnOpConfig(Config):
        an_optional_nested: Dict[str, ANestedConfig]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.an_optional_nested["foo"].a_str == "foo"
        assert config.an_optional_nested["bar"].a_str == "bar"

    @job
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
def test_struct_config_map_different_key_type(key_type: Type, keys: List[Any]):
    class AnOpConfig(Config):
        my_dict: Dict[key_type, int]

    executed = {}

    @op
    def a_struct_config_op(config: AnOpConfig):
        executed["yes"] = True
        assert config.my_dict == {keys[0]: 1, keys[1]: 2}

    @job
    def a_job():
        a_struct_config_op()

    a_job.execute_in_process(
        {"ops": {"a_struct_config_op": {"config": {"my_dict": {keys[0]: 1, keys[1]: 2}}}}}
    )
    assert executed["yes"]


def test_descriminated_unions():
    class Cat(Config):
        pet_type: Literal["cat"]
        meows: int

    class Dog(Config):
        pet_type: Literal["dog"]
        barks: float

    class Lizard(Config):
        pet_type: Literal["reptile", "lizard"]
        scales: bool

    class OpConfigWithUnion(Config):
        pet: Union[Cat, Dog, Lizard] = Field(..., discriminator="pet_type")
        n: int

    executed = {}

    @op
    def a_struct_config_op(config: OpConfigWithUnion):
        if config.pet.pet_type == "cat":
            assert config.pet.meows == 2
        elif config.pet.pet_type == "dog":
            assert config.pet.barks == 3.0
        elif config.pet.pet_type == "lizard":
            assert config.pet.scales
        assert config.n == 4

        executed["yes"] = True

    @job
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
    with pytest.raises(DagsterInvalidConfigError):
        a_job.execute_in_process(
            {"ops": {"a_struct_config_op": {"config": {"pet": {"octopus": {"meows": 2}}, "n": 4}}}}
        )

    # Disallow passing multiple discriminated union values
    with pytest.raises(DagsterInvalidConfigError):
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


def test_nested_discriminated_unions():
    class Poodle(Config):
        breed_type: Literal["poodle"]
        fluffy: bool

    class Dachshund(Config):
        breed_type: Literal["dachshund"]
        long: bool

    class Cat(Config):
        pet_type: Literal["cat"]
        meows: int

    class Dog(Config):
        pet_type: Literal["dog"]
        barks: float
        breed: Union[Poodle, Dachshund] = Field(..., discriminator="breed_type")

    class OpConfigWithUnion(Config):
        pet: Union[Cat, Dog] = Field(..., discriminator="pet_type")
        n: int

    executed = {}

    @op
    def a_struct_config_op(config: OpConfigWithUnion):
        assert config.pet.pet_type == "dog"
        assert isinstance(config.pet, Dog)
        assert config.pet.breed.breed_type == "poodle"
        assert isinstance(config.pet.breed, Poodle)
        assert config.pet.breed.fluffy

        executed["yes"] = True

    @job
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
