from typing import Annotated

import dagster as dg
from dagster._config.config_type import ConfigTypeKind
from pydantic import Field


def test_new_config_descriptions_and_defaults():
    class ANestedOpConfig(dg.Config):
        an_int: Annotated[int, Field(description="An int")]

    class AnOpConfig(dg.Config):
        """Config for my new op."""

        a_string: str = Field(description="A string")
        nested: ANestedOpConfig = Field(description="A nested config")

    @dg.op
    def a_new_config_op(config: AnOpConfig):
        pass

    # test fields are inferred correctly
    assert a_new_config_op.config_schema.config_type.kind == ConfigTypeKind.STRICT_SHAPE  # pyright: ignore[reportOptionalMemberAccess]
    assert list(a_new_config_op.config_schema.config_type.fields.keys()) == ["a_string", "nested"]  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert a_new_config_op.config_schema.description == "Config for my new op."
    assert a_new_config_op.config_schema.config_type.fields["a_string"].description == "A string"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    assert (
        a_new_config_op.config_schema.config_type.fields["nested"].description == "A nested config"  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    )
    assert (
        a_new_config_op.config_schema.config_type.fields["nested"]  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
        .config_type.fields["an_int"]
        .description
        == "An int"
    )
