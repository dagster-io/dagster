from dagster import check


def get_loadable_targets(python_file, module_name, working_directory):
    from dagster.cli.workspace.autodiscovery import (
        loadable_targets_from_python_file,
        loadable_targets_from_python_module,
    )

    if python_file:
        return loadable_targets_from_python_file(python_file, working_directory)
    elif module_name:
        return loadable_targets_from_python_module(module_name)
    else:
        check.failed('invalid')
