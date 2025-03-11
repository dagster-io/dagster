from collections.abc import Iterator
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

import yaml

from dagster_dg.context import DgContext


@contextmanager
def temp_workspace_file(dg_context: DgContext) -> Iterator[str]:
    with NamedTemporaryFile(mode="w+", delete=True) as temp_workspace_file:
        entries = []
        if dg_context.is_project:
            entries.append(_workspace_entry_for_project(dg_context))
        elif dg_context.is_workspace:
            for project_spec in dg_context.project_specs:
                project_context: DgContext = dg_context.with_root_path(project_spec.path)
                entries.append(_workspace_entry_for_project(project_context))
        yaml.dump({"load_from": entries}, temp_workspace_file)
        temp_workspace_file.flush()
        yield temp_workspace_file.name


def _workspace_entry_for_project(dg_context: DgContext) -> dict[str, dict[str, str]]:
    entry = {
        "working_directory": str(dg_context.root_path),
        "module_name": str(dg_context.code_location_target_module_name),
        "location_name": dg_context.code_location_name,
    }
    if dg_context.use_dg_managed_environment:
        entry["executable_path"] = str(dg_context.project_python_executable)
    return {"python_module": entry}


def format_forwarded_option(option: str, value: object) -> list[str]:
    return [] if value is None else [option, str(value)]
