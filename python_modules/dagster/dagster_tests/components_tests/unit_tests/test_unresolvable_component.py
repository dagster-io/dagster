import dagster as dg
import pytest
from dagster.components.core.tree import ComponentTreeException
from dagster.components.testing.utils import create_defs_folder_sandbox


class UnresolvableComponent(dg.Component, dg.Model):
    """This component class does not subclass Resolvable."""

    some_field: str

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions: ...


def test_unresolvable_component():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            UnresolvableComponent,
            defs_yaml_contents={
                "type": "dagster_tests.components_tests.unit_tests.test_unresolvable_component.UnresolvableComponent",
                # this component is not resolvable and so cannot have attributes
                "attributes": {"some_field": "foo"},
            },
        )
        with pytest.raises(ComponentTreeException):
            with sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, defs):
                ...
