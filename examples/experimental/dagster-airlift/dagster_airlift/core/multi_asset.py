from importlib import import_module
from pathlib import Path
from typing import List, Literal, Optional, Sequence, Type, Union

from dagster import AssetDep, AssetKey, AssetSpec, Definitions, multi_asset
from dagster_blueprints import YamlBlueprintsLoader
from dagster_blueprints.blueprint import Blueprint
from pydantic import BaseModel


class AssetSpecModel(BaseModel):
    key: str
    deps: List[str] = []


class PythonFn(BaseModel):
    module_name: str
    fn_name: str


class PythonDefs(Blueprint):
    type: Literal["multi_asset"] = "multi_asset"
    specs: List[AssetSpecModel]
    python_fn_pointer: Optional[PythonFn] = None
    name: Optional[str] = None

    def build_defs(self) -> Definitions:
        asset_specs = [
            AssetSpec(
                key=AssetKey.from_user_string(spec.key),
                deps=[AssetDep(AssetKey.from_user_string(dep)) for dep in spec.deps],
            )
            for spec in self.specs
        ]
        abridged_file_name = self.source_file_name.split(".")[0]

        @multi_asset(
            specs=asset_specs,
            name=self.name or abridged_file_name,
        )
        def _multi_asset() -> None:
            if self.python_fn_pointer:
                module = import_module(self.python_fn_pointer.module_name)
                compute_fn = getattr(module, self.python_fn_pointer.fn_name)
                compute_fn()

        return Definitions(assets=[_multi_asset])


# Eventually, we should be able to provide many different types of blueprints all from the same fxn call and same path.
# But we can't currently handle multiple blueprint types in the same directory.
def load_defs_from_yaml(
    yaml_path: Path, defs_cls: Union[Type[Blueprint], Type[Sequence[Blueprint]]]
) -> Definitions:
    return YamlBlueprintsLoader(
        path=yaml_path,
        per_file_blueprint_type=defs_cls,
    ).load_defs()
