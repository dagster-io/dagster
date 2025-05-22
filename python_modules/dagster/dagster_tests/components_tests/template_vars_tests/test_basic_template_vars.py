from typing import Any

from dagster._core.definitions.definitions_class import Definitions
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Model

from dagster_tests.components_tests.utils import load_context_and_component_for_test


class ComponentWithAdditionalScope(Component, Resolvable, Model):
    value: str

    @classmethod
    def get_additional_scope(cls) -> dict[str, Any]:
        return {
            "foo": "value_for_foo",
            "a_udf": lambda: "a_udf_value",
            "a_udf_with_args": lambda x: f"a_udf_value_{x}",
        }

    def build_defs(self, context: ComponentLoadContext) -> Definitions: ...


def test_basic_additional_scope_hardcoded_value():
    load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "a_value"}
    )

    assert component.value == "a_value"


def test_basic_additional_scope_scope_var():
    load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "{{ foo }}"}
    )

    assert component.value == "value_for_foo"


def test_basic_additional_scope_scope_udf_no_args():
    load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "{{ a_udf() }}"}
    )

    assert component.value == "a_udf_value"


def test_basic_additional_scope_scope_udf_with_args():
    load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "{{ a_udf_with_args('1') }}"}
    )

    assert component.value == "a_udf_value_1"


class ComponentWithInjectedScope(Component, Resolvable, Model):
    value: str

    def build_defs(self, context: ComponentLoadContext) -> Definitions: ...


def test_basic_injected_scope_var():
    load_context, component = load_context_and_component_for_test(
        ComponentWithInjectedScope,
        {"value": "{{ foo }}"},
        injectables_module="dagster_tests.components_tests.template_vars_tests.template_vars",
    )

    assert component.value == "value_for_foo"


def test_basic_scope_udf_no_args():
    load_context, component = load_context_and_component_for_test(
        ComponentWithInjectedScope,
        {"value": "{{ a_udf() }}"},
        injectables_module="dagster_tests.components_tests.template_vars_tests.template_vars",
    )

    assert component.value == "a_udf_value"


def test_basic_scope_udf_with_args():
    load_context, component = load_context_and_component_for_test(
        ComponentWithInjectedScope,
        {"value": "{{ a_udf_with_args('1') }}"},
        injectables_module="dagster_tests.components_tests.template_vars_tests.template_vars",
    )

    assert component.value == "a_udf_value_1"
