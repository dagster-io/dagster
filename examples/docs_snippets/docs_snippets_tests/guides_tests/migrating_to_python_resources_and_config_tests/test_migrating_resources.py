from docs_snippets.guides.dagster.migrating_to_python_resources_and_config.migrating_resources import (
    convert_resource,
    initial_code_base,
    new_resource_code_contextmanager,
    new_style_resource_on_context,
    new_style_resource_on_param,
    new_third_party_resource_factory_pattern,
    old_resource_code_contextmanager,
    old_third_party_resource,
)


def test_initial_code_base() -> None:
    defs = initial_code_base()
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success


def test_convert_resource() -> None:
    assert convert_resource


def test_new_style_resource_on_context() -> None:
    assert new_style_resource_on_context


def test_new_style_resource_on_param() -> None:
    assert new_style_resource_on_param


def test_old_third_party_resource() -> None:
    defs = old_third_party_resource()
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success


def test_old_resource_code_contextmanager() -> None:
    defs = old_resource_code_contextmanager()
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success


def test_new_resource_code_contextmanager() -> None:
    defs = new_resource_code_contextmanager()
    assert defs.get_implicit_global_asset_job_def().execute_in_process().success


def test_new_third_party_resource_factory_pattern() -> None:
    defs = new_third_party_resource_factory_pattern()
    assert defs.get_job_def("new_asset_job").execute_in_process().success
