from dagster._core.definitions.module_loaders.utils import find_modules_in_package


def test_find_modules_in_package():
    from dagster_tests.definitions_tests.module_loader_tests import asset_package, checks_module

    modules = set(find_modules_in_package(asset_package))
    assert len(modules) == 5

    modules = set(find_modules_in_package(checks_module))
    assert len(modules) == 3
