import importlib.util
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Mapping, Optional, Sequence, Union


class AliasedModuleFinder(MetaPathFinder):

    def __init__(self, alias_map: Mapping[str, str]):
        self.alias_map = alias_map
        self.prefixes = set(alias_map.keys())

    def find_spec(
        self,
        fullname: str,
        _path: Optional[Sequence[Union[bytes, str]]] = None,
        _target: Optional[ModuleType] = None,
    ) -> Optional[ModuleSpec]:
        head = next((p for p in self.prefixes if fullname.startswith(p)), None)
        if head is not None:
            base_name = self.alias_map[fullname] + fullname[len(head):]
            base_spec = importlib.util.find_spec(base_name)
            assert base_spec
            return ModuleSpec(
                fullname,
                AliasedModuleLoader(fullname, base_spec),
                origin=base_spec.origin,
                is_package=base_spec.submodule_search_locations is not None,
            )
        else:
            return None

class AliasedModuleLoader(Loader):

    def __init__(self, alias: str, base_spec: ModuleSpec):
        self.alias = alias
        self.base_spec = base_spec
        self.base_name = base_spec.name
        assert base_spec.loader
        self.base_loader = base_spec.loader

    # Use the target's `create_module`. If it returns None, it just means use default module
    # creation logic.
    def create_module(self, spec: ModuleSpec) -> Optional[ModuleType]:
        return self.base_loader.create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        # target already loaded
        if self.base_name in sys.modules:
            sys.modules[self.alias] = sys.modules[self.base_name]

        # target not yet loaded
        else:
            sys.modules[self.base_name] = module
            sys.modules[self.alias] = module
            try:
                self.base_loader.exec_module(module)
            except BaseException:
                del sys.modules[self.base_name]
                del sys.modules[self.alias]
                raise

    def module_repr(self, module: ModuleType) -> str:
        return self.base_loader.module_repr(module)

