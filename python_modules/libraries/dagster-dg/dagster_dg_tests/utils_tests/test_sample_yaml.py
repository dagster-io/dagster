from collections.abc import Sequence
from typing import Annotated

from dagster_components import Model, Resolvable, ResolvableFieldInfo
from dagster_dg.docs import generate_sample_yaml


class SampleSubModel(Model):
    str_field: str
    int_field: int


class SampleModel(Model, Resolvable):
    sub_scoped: Annotated[SampleSubModel, ResolvableFieldInfo(required_scope={"outer_scope"})]
    sub_optional: SampleSubModel
    sub_list: Sequence[SampleSubModel]


def test_generate_sample_yaml():
    yaml = generate_sample_yaml(
        component_type=".sample", json_schema=SampleModel.model_json_schema()
    )
    assert (
        yaml
        == """type: .sample

attributes:
  sub_scoped: # Available scope: {'outer_scope'}
    str_field: '...' # Available scope: {'outer_scope'}
    int_field: 0 # Available scope: {'outer_scope'}
  sub_optional:
    str_field: '...'
    int_field: 0
  sub_list:
    - str_field: '...'
      int_field: 0
"""
    )
