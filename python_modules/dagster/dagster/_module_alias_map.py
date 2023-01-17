import importlib
import importlib.util
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder
from types import ModuleType
from typing import Mapping, Optional, Sequence, Union


# The AliasedModuleFinder should be inserted in front of the built-in PathFinder.
def get_meta_path_insertion_index() -> int:
    for i in range(len(sys.meta_path)):
        finder = sys.meta_path[i]
        if isinstance(finder, type) and issubclass(finder, PathFinder):
            return i
    raise Exception(
        "Could not find the built-in PathFinder in sys.meta_path-- cannot insert the"
        " AliasedModuleFinder"
    )


class AliasedModuleFinder(MetaPathFinder):
    def __init__(self, alias_map: Mapping[str, str]):
        self.alias_map = alias_map

    def find_spec(
        self,
        fullname: str,
        _path: Optional[Sequence[Union[bytes, str]]] = None,
        _target: Optional[ModuleType] = None,
    ) -> Optional[ModuleSpec]:
        head = next((k for k in self.alias_map.keys() if fullname.startswith(k)), None)
        if head is not None:
            base_name = self.alias_map[head] + fullname[len(head) :]
            base_spec = importlib.util.find_spec(base_name)
            assert base_spec, f"Could not find module spec for {base_name}."
            return ModuleSpec(
                fullname,
                AliasedModuleLoader(fullname, base_spec),
                origin=base_spec.origin,
                is_package=base_spec.submodule_search_locations is not None,
            )
        else:
            return None


# Key reference to understand the load process:
#   https://docs.python.org/3/reference/import.html#loading


# While it is possible to override `Loader.create_module` to simply return the base module, this
# is undesirable because the import system modifies the module's metadata attributes after
# creation and outside of our control. This means that, if we simply had:
#
#     def create_module(self, spec):
#         return importlib.import_module(self.base_spec_name)
#
# The returned base module would have its name etc modified, e.g. the already-loaded
# `dagster._core` would be renamed to alias `dagster.core`. To avoid this, we let the import system
# generate a module using default logic, then simply discard this module in `exec_module` (the final
# step), where it is passed in. This is the point at which we swap in the base module, which we
# obtain through `importlib.import_module` (like a standard import statetment, this will simply
# returned the cached module from `sys.modules` if it has already been loaded). The swap is done by
# simply replacing the dummy module (already stored in `sys.modules` outside of our control) with
# the imported base module.
class AliasedModuleLoader(Loader):
    def __init__(self, alias: str, base_spec: ModuleSpec):
        self.alias = alias
        self.base_spec = base_spec

    def exec_module(self, _module: ModuleType) -> None:
        base_module = importlib.import_module(self.base_spec.name)
        sys.modules[self.alias] = base_module

    def module_repr(self, module: ModuleType) -> str:
        assert self.base_spec.loader
        return self.base_spec.loader.module_repr(module)
