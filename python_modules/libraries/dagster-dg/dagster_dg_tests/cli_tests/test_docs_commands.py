from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result, isolated_components_venv

# ########################
# ##### COMPONENT TYPE
# ########################


def test_docs_component_type_success():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "docs", "component-type", "dagster_test.components.SimpleAssetComponent"
        )
        assert_runner_result(result)


def _includes_ignore_indent(text: str, substr: str) -> bool:
    # ensure that the substr is present in the text, ignoring any leading whitespace on each
    # line of text
    substr_no_leading_whitespace = "\n".join([line.lstrip() for line in substr.split("\n")])
    text_no_leading_whitespace = "\n".join([line.lstrip() for line in text.split("\n")])
    return substr_no_leading_whitespace in text_no_leading_whitespace


def test_docs_component_type_success_output_console():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_components_venv(runner),
    ):
        result = runner.invoke(
            "docs",
            "component-type",
            "dagster_test.components.ComplexAssetComponent",
            "--output",
            "cli",
        )
        assert_runner_result(result)
        assert "<html" in result.output
        assert "An asset that has a complex schema." in result.output

        # Test that examples propagate into docs
        assert "value: example_for_value" in result.output
        assert _includes_ignore_indent(
            result.output,
            """
list_value:
    - example_for_list_value_1
    - example_for_list_value_2
        """,
        )
        assert _includes_ignore_indent(
            result.output,
            """
obj_value:
    key_1: value_1
    key_2: value_2
        """,
        )
