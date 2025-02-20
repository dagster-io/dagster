from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result, isolated_components_venv

# ########################
# ##### COMPONENT TYPE
# ########################


def test_docs_component_type_success():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke("docs", "component-type", "simple_asset@dagster_components.test")
        assert_runner_result(result)


def test_docs_component_type_success_output_console():
    with ProxyRunner.test() as runner, isolated_components_venv(runner):
        result = runner.invoke(
            "docs",
            "component-type",
            "complex_schema_asset@dagster_components.test",
            "--output",
            "cli",
        )
        assert_runner_result(result)
        assert "<html" in result.output
        assert "An asset that has a complex params schema." in result.output
