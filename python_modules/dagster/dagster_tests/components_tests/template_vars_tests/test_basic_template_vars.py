import sys
from collections.abc import Callable

import dagster as dg
import pytest
from dagster.components.core.context import ComponentLoadContext

from dagster_tests.components_tests.utils import load_context_and_component_for_test


class ComponentWithAdditionalScope(dg.Component, dg.Resolvable, dg.Model):
    value: str

    @staticmethod
    @dg.template_var
    def foo() -> str:
        return "value_for_foo"

    @staticmethod
    @dg.template_var
    def a_udf() -> Callable:
        return lambda: "a_udf_value"

    @staticmethod
    @dg.template_var
    def a_udf_with_args() -> Callable:
        return lambda x: f"a_udf_value_{x}"

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions: ...


def test_basic_additional_scope_hardcoded_value():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "a_value"}
    )

    assert component.value == "a_value"


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="staticmethod behavior differs on python 3.9"
)
def test_basic_additional_scope_scope_var():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "{{ foo }}"}
    )

    assert component.value == "value_for_foo"


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="staticmethod behavior differs on python 3.9"
)
def test_basic_additional_scope_scope_udf_no_args():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "{{ a_udf() }}"}
    )

    assert component.value == "a_udf_value"


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="staticmethod behavior differs on python 3.9"
)
def test_basic_additional_scope_scope_udf_with_args():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithAdditionalScope, {"value": "{{ a_udf_with_args('1') }}"}
    )

    assert component.value == "a_udf_value_1"


class ComponentWithInjectedScope(dg.Component, dg.Resolvable, dg.Model):
    value: str

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions: ...


def test_basic_injected_scope_var():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithInjectedScope,
        {"value": "{{ foo }}"},
        template_vars_module="dagster_tests.components_tests.template_vars_tests.template_vars",
    )

    assert component.value == "value_for_foo"


def test_basic_scope_udf_no_args():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithInjectedScope,
        {"value": "{{ a_udf() }}"},
        template_vars_module="dagster_tests.components_tests.template_vars_tests.template_vars",
    )

    assert component.value == "a_udf_value"


def test_basic_scope_udf_with_args():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithInjectedScope,
        {"value": "{{ a_udf_with_args('1') }}"},
        template_vars_module="dagster_tests.components_tests.template_vars_tests.template_vars",
    )

    assert component.value == "a_udf_value_1"


class ComponentWithContextTemplateVars(dg.Component, dg.Resolvable, dg.Model):
    value: str

    @staticmethod
    @dg.template_var
    def no_context_var() -> str:
        return "no_context_value"

    @staticmethod
    @dg.template_var
    def context_var(context: ComponentLoadContext) -> str:
        return f"context_value_{context.path.name}"

    @staticmethod
    @dg.template_var
    def context_udf(context: ComponentLoadContext) -> Callable:
        return lambda x: f"context_udf_{x}_{context.path.name}"

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions: ...


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="staticmethod behavior differs on python 3.9"
)
def test_static_template_var_with_context():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithContextTemplateVars, {"value": "{{ context_var }}"}
    )

    assert component.value == "context_value_dagster"


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="staticmethod behavior differs on python 3.9"
)
def test_static_template_var_mixed_context():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithContextTemplateVars, {"value": "{{ no_context_var }}"}
    )

    assert component.value == "no_context_value"


@pytest.mark.skipif(
    sys.version_info < (3, 10), reason="staticmethod behavior differs on python 3.9"
)
def test_static_template_udf_with_context():
    _load_context, component = load_context_and_component_for_test(
        ComponentWithContextTemplateVars, {"value": "{{ context_udf('test') }}"}
    )

    assert component.value == "context_udf_test_dagster"
