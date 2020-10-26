from dagster import check
from dagster.core.definitions.reconstructable import (
    load_def_in_module,
    load_def_in_package,
    load_def_in_python_file,
)


def get_loadable_targets(python_file, module_name, package_name, working_directory, attribute):
    from dagster.cli.workspace.autodiscovery import (
        LoadableTarget,
        loadable_targets_from_python_file,
        loadable_targets_from_python_module,
        loadable_targets_from_python_package,
    )

    if python_file:
        return (
            [
                LoadableTarget(
                    attribute, load_def_in_python_file(python_file, attribute, working_directory)
                )
            ]
            if attribute
            else loadable_targets_from_python_file(python_file, working_directory)
        )
    elif module_name:
        return (
            [LoadableTarget(attribute, load_def_in_module(module_name, attribute))]
            if attribute
            else loadable_targets_from_python_module(module_name)
        )
    elif package_name:
        return (
            [LoadableTarget(attribute, load_def_in_package(package_name, attribute))]
            if attribute
            else loadable_targets_from_python_package(package_name)
        )
    else:
        check.failed("invalid")
