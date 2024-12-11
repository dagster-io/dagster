import importlib
import importlib.metadata
import re
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Iterable, Iterator, Optional, Sequence, Tuple, Type

from dagster._core.errors import DagsterError
from packaging.markers import Marker
from packaging.requirements import Requirement

if TYPE_CHECKING:
    from dagster_components.core.component import Component

# The sole interface of this module is `get_registered_components_from_python_environment`. This function
# returns finds all components registered in the current Python environment by using the Python
# entry points API. Here is how it works:
#
# - Any installed package can declare dagster components under the `dagster.components` entry point
#   group.
# - The name of an entry in the `dagster.components` entry point group is expected to have one of
#   two forms:
#   - <pkg_name>: This is an unconditional entry point that is always loaded.
#   - <pkg_name>.__extras__.<extra_name>: This is a conditional entry point that is only
#     loaded if the extra <extra_name> is installed for the package <pkg_name>.
# - The entry point value is expected to be a module that contains components. Components are marked
#   with the `@component` decorator. The module and submodules will be recursively searched for
#   components, with the exception that any submodule named __extras__ will be ignored. This allows
#   copmonents defined in __extras__ to be loaded conditionally dependent by dedicated entry points.
#
# Example pyproject.toml:
#
# [project.entry-points]
# "dagster.components" = {
#     my_pkg = my_pkg.lib",
#     my_pkg.__extras__.extra_1 = "my_pkg.lib.__extras__.extra_1",
#     my_pkg.__extras__.extra_2 = "my_pkg.lib.__extras__.extra_2",
# }

_COMPONENTS_ENTRY_POINT_GROUP = "dagster.components"
_EXTRAS_SEPARATOR = ".__extras__."


def get_registered_components_from_python_environment() -> Iterator[Tuple[str, Type["Component"]]]:
    for entry_point in _get_filtered_entry_points(_COMPONENTS_ENTRY_POINT_GROUP):
        root_module = entry_point.load()
        if not isinstance(root_module, ModuleType):
            raise DagsterError(
                f"Invalid entry point {entry_point.name} in group {_COMPONENTS_ENTRY_POINT_GROUP}. "
                f"Value expected to be a module, got {root_module}."
            )
        dist_name, _ = _parse_entry_point_name(entry_point.name)
        for component in _get_registered_components_in_package(root_module):
            yield (dist_name, component)


def _get_filtered_entry_points(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    entry_points = _get_all_entry_points(group)
    return [ep for ep in entry_points if _entry_point_matches_environment(ep)]


def _get_all_entry_points(group: str) -> Sequence[importlib.metadata.EntryPoint]:
    if sys.version_info >= (3, 10):
        return importlib.metadata.entry_points(group=group)
    else:
        return importlib.metadata.entry_points().get(group, [])


def _parse_entry_point_name(entry_point: str) -> Tuple[str, Optional[str]]:
    name_parts = entry_point.split(_EXTRAS_SEPARATOR, 1)
    if len(name_parts) == 1:
        return name_parts[0], None
    else:
        return name_parts[0], name_parts[1]


def _entry_point_matches_environment(entry_point: importlib.metadata.EntryPoint) -> bool:
    name_parts = entry_point.name.split(_EXTRAS_SEPARATOR, 1)

    # Entry point does not correspond to an extra, unconditional match
    if len(name_parts) == 1:
        return True

    # Entry point corresponds to an extra, check if the extra is installed
    else:
        distribution_package, extra = name_parts
        return _is_extra_installed(distribution_package, extra)


def _is_extra_installed(distribution_package: str, extra: str) -> bool:
    pkg_metadata = importlib.metadata.metadata(distribution_package)
    dependencies = [Requirement(req_str) for req_str in pkg_metadata.get_all("Requires-Dist", [])]
    extra_dependencies = [
        dep
        for dep in dependencies
        if dep.marker
        and re.search(re.compile(f"extra == ['\"]{extra}['\"]"), str(dep.marker))
        # and f"extra == '{extra}'" in str(dep.marker)
        and _marker_matches_environment(dep.marker)
    ]
    return all(_is_requirement_installed(dep) for dep in extra_dependencies)


def _marker_matches_environment(marker: Marker) -> bool:
    # Remove the 'extra == ' part of the marker. This is appended by importlib metadata but not
    # intended to be evaluated.
    clean_marker = re.sub(re.compile("( and )?extra == ['\"][^']+['\"]"), "", str(marker)).strip()

    # The marker consisted entirely of the extra specification, there are no additional conditions
    if clean_marker == "":
        return True
    # The marker had additional conditions such as python_version, sys_platform constraints.
    # Evaluate them with the packaging.marker API.
    else:
        return Marker(clean_marker).evaluate()


def _is_requirement_installed(requirement: Requirement) -> bool:
    try:
        dist = importlib.metadata.distribution(requirement.name)
    except importlib.metadata.PackageNotFoundError:
        return False

    # Check version constraints
    if requirement.specifier:
        if not requirement.specifier.contains(dist.version, prereleases=True):
            return False

    if requirement.extras:
        for extra in requirement.extras:
            if not _is_extra_installed(requirement.name, extra):
                return False

    return True


def _get_registered_components_in_package(root_module: ModuleType) -> Iterable[Type["Component"]]:
    from dagster._core.definitions.load_assets_from_modules import (
        find_modules_in_package,
        find_subclasses_in_module,
    )

    from dagster_components.core.component import Component, is_registered_component

    for module in find_modules_in_package(root_module):
        relative_name = module.__name__.removeprefix(root_module.__name__)

        # Ignore __extras__ submodules. When explicitly loading an extra, __extras__ will be in the
        # root module.
        if "__extras__" in relative_name:
            continue
        for component in find_subclasses_in_module(module, (Component,)):
            if is_registered_component(component):
                yield component
