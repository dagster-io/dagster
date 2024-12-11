"""These tests are included here instead of in test_serdes, because the model_tests run on both
Pydantic 1 and 2, while the general_tests do not.
"""

import pytest
from dagster._model import DagsterModel
from dagster._serdes.errors import SerializationError
from dagster._serdes.serdes import (
    WhitelistMap,
    _whitelist_for_serdes,
    deserialize_value,
    pack_value,
    serialize_value,
    unpack_value,
)
from pydantic import Field


def test_pydantic_alias():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class SomeDagsterModel(DagsterModel):
        unaliased_id: int = Field(..., alias="id_alias")
        name: str

    o = SomeDagsterModel(id_alias=5, name="fdsk")
    packed_o = pack_value(o, whitelist_map=test_env)
    assert packed_o == {"__class__": "SomeDagsterModel", "id_alias": 5, "name": "fdsk"}
    assert unpack_value(packed_o, whitelist_map=test_env, as_type=SomeDagsterModel) == o

    ser_o = serialize_value(o, whitelist_map=test_env)
    assert deserialize_value(ser_o, whitelist_map=test_env) == o


def test_pydantic_alias_generator():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class SomeDagsterModel(DagsterModel):
        id: int = Field(...)
        name: str

        class Config:
            alias_generator = lambda field_name: f"{field_name}_alias"

    o = SomeDagsterModel(id_alias=5, name_alias="fdsk")  # pyright: ignore[reportCallIssue]
    packed_o = pack_value(o, whitelist_map=test_env)
    assert packed_o == {"__class__": "SomeDagsterModel", "id_alias": 5, "name_alias": "fdsk"}
    assert unpack_value(packed_o, whitelist_map=test_env, as_type=SomeDagsterModel) == o

    ser_o = serialize_value(o, whitelist_map=test_env)
    assert deserialize_value(ser_o, whitelist_map=test_env) == o


def test_pydantic_serialization_alias():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class SomeDagsterModel(DagsterModel):
        unaliased_id: int = Field(..., serialization_alias="id_alias")
        name: str

    o = SomeDagsterModel(unaliased_id=5, name="fdsk")
    with pytest.raises(
        SerializationError,
        match="Can't serialize pydantic models with serialization or validation aliases.",
    ):
        serialize_value(o, whitelist_map=test_env)

    with pytest.raises(
        SerializationError,
        match="Can't serialize pydantic models with serialization or validation aliases.",
    ):
        pack_value(o, whitelist_map=test_env)


def test_pydantic_validation_alias():
    test_env = WhitelistMap.create()

    @_whitelist_for_serdes(test_env)
    class SomeDagsterModel(DagsterModel):
        unaliased_id: int = Field(..., validation_alias="id_alias")
        name: str

    o = SomeDagsterModel(id_alias=5, name="fdsk")  # pyright: ignore[reportCallIssue]
    with pytest.raises(
        SerializationError,
        match="Can't serialize pydantic models with serialization or validation aliases.",
    ):
        serialize_value(o, whitelist_map=test_env)

    with pytest.raises(
        SerializationError,
        match="Can't serialize pydantic models with serialization or validation aliases.",
    ):
        pack_value(o, whitelist_map=test_env)
