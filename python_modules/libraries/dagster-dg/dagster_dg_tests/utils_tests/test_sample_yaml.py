from collections.abc import Sequence
from typing import Annotated

from dagster_components import ComponentSchemaBaseModel, ResolvableFieldInfo
from dagster_dg.docs import generate_sample_yaml


class SampleSubSchema(ComponentSchemaBaseModel):
    str_field: str
    int_field: int


class SampleSchema(ComponentSchemaBaseModel):
    sub_scoped: Annotated[SampleSubSchema, ResolvableFieldInfo(additional_scope={"outer_scope"})]
    sub_optional: SampleSubSchema
    sub_list: Sequence[SampleSubSchema]


def test_generate_sample_yaml():
    yaml = generate_sample_yaml(
        component_type=".sample", json_schema=SampleSchema.model_json_schema()
    )
    assert (
        yaml
        == """type: .sample

params:
  sub_scoped: # Available scope: {'outer_scope'}
    str_field: '...'
    int_field: 0
  sub_optional:
    str_field: '...'
    int_field: 0
  sub_list:
    - str_field: '...'
      int_field: 0
"""
    )
