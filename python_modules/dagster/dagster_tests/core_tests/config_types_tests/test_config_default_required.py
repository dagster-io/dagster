import pytest

from dagster import Field, execute_solid, solid


def test_default_implies_not_required_field_correct():
    @solid(config_schema={"default_to_one": Field(int, default_value=1)})
    def return_default_to_one(context):
        return context.solid_config["default_to_one"]

    default_to_one_field = return_default_to_one.config_field.config_type.fields["default_to_one"]
    assert default_to_one_field.is_required is False


def test_default_implies_not_required_execute_solid():
    @solid(config_schema={"default_to_one": Field(int, default_value=1)})
    def return_default_to_one(context):
        return context.solid_config["default_to_one"]

    # This currently throws. It should not require configuration as the
    # the default value should make it *not* required.
    execute_solid(return_default_to_one)
