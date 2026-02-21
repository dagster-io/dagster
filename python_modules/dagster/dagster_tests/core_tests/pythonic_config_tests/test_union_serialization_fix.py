import dagster as dg
from pydantic import Field
from typing import Union, Literal

def test_union_config_revalidation_fix():
    class ConfigA(dg.Config):
        t: Literal["a"] = "a"
        v: int

    class ConfigB(dg.Config):
        t: Literal["b"] = "b"

    class MasterConfig(dg.Config):
        union_field: Union[ConfigA, ConfigB] = Field(discriminator="t")

    # דימוי של המרת אובייקט למילון (כמו שקורה ב-dump)
    data = {"union_field": {"t": "a", "v": 10}}
    
    # לפני התיקון שלך - השורה הזו קרסה
    revalidated = MasterConfig(**data)
    
    assert revalidated.union_field.t == "a"
    assert revalidated.union_field.v == 10