from typing import Literal, Union

import dagster as dg
from pydantic import Field


def test_union_config_revalidation_fix():
    class ConfigA(dg.Config):
        t: Literal["a"] = "a"
        v: int

    class ConfigB(dg.Config):
        t: Literal["b"] = "b"

    class MasterConfig(dg.Config):
        union_field: Union[ConfigA, ConfigB] = Field(discriminator="t")

    data = {"union_field": {"t": "a", "v": 10}}
    
    revalidated = MasterConfig(**data)
    
    assert revalidated.union_field.t == "a"
    assert revalidated.union_field.v == 10