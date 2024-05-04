import inspect
from abc import abstractmethod
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Sequence, Set, Type, Union

import yaml

from dagster import (
    AssetSpec,
    _check as check,
    multi_asset,
)
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster._core.storage.io_manager import IOManager
from dagster._seven import is_subclass

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

if TYPE_CHECKING:
    from dagster._core.definitions.definitions_class import Definitions


def deps_from_asset_manifest(raw_asset_manifest_obj: dict) -> Sequence[CoercibleToAssetDep]:
    if not raw_asset_manifest_obj or "deps" not in raw_asset_manifest_obj:
        return []

    return [
        AssetKey.from_user_string(dep) if isinstance(dep, str) else dep
        for dep in raw_asset_manifest_obj["deps"]
    ]


class NopeAssetManifest:
    def __init__(
        self,
        *,
        invocation_target_manifest: "NopeInvocationTargetManifest",
        asset_manifest_obj: dict,
        group_name: str,
        asset_key_parts: List[str],
    ) -> None:
        self.invocation_target_manifest = invocation_target_manifest
        self.asset_manifest_obj = asset_manifest_obj or {}
        self._group_name = group_name
        self.asset_key_parts = asset_key_parts

    @property
    def deps(self) -> Sequence[CoercibleToAssetDep]:
        return deps_from_asset_manifest(self.asset_manifest_obj)

    @property
    def asset_key(self) -> CoercibleToAssetKey:
        return AssetKey([self.group_name] + self.asset_key_parts)

    @property
    def description(self) -> Optional[str]:
        return self.asset_manifest_obj.get("description", "")

    @property
    def code_version(self) -> Optional[str]:
        return None

    @property
    def group_name(self) -> str:
        return self._group_name

    @property
    def tags(self) -> dict:
        return self.asset_manifest_obj.get("tags", {})

    @property
    def metadata(self) -> dict:
        return self.asset_manifest_obj.get("metadata", {})

    @property
    def owners(self) -> List[str]:
        return self.asset_manifest_obj.get("owners", [])

    @property
    def asset_spec(self) -> AssetSpec:
        return AssetSpec(
            key=self.asset_key,
            deps=self.deps,
            description=self.description,
            group_name=self.group_name,
            tags=self.tags,
            metadata=self.metadata,
            owners=self.owners,
            code_version=self.code_version,
        )


class NopeInvocationTargetManifest:
    file_path: Path
    asset_spec: AssetSpec

    def __init__(
        self,
        *,
        group_name: str,
        op_name: str,
        full_manifest_obj: dict,
        asset_manifest_class: Type,
        # tempoarty until we figure this out
        full_manifest_path: Optional[Path],
        python_script_path: Optional[Path],
    ) -> None:
        self._group_name = group_name
        self.full_manifest_path = full_manifest_path
        self.full_manifest_obj = full_manifest_obj
        self.asset_manifest_class = asset_manifest_class
        self._op_name = op_name
        self.python_script_path = python_script_path

    @classmethod
    def from_opinionated_layout_path(
        cls, *, group_name: str, manifest_path: Path, asset_manifest_class: Type
    ):
        file_name_parts = manifest_path.stem.split(".")
        op_name = file_name_parts[-1]
        full_manifest_obj = yaml.load(manifest_path.read_text(), Loader=Loader)
        script_path = manifest_path.parent / Path(full_manifest_obj["script"])
        return cls(
            group_name=group_name,
            full_manifest_obj=full_manifest_obj,
            asset_manifest_class=asset_manifest_class,
            op_name=op_name,
            full_manifest_path=manifest_path,
            python_script_path=script_path,
        )

    @property
    def target(self) -> str:
        return self.full_manifest_obj["target"]

    @property
    def asset_manifests(self) -> Sequence[NopeAssetManifest]:
        raw_asset_manifests = self.full_manifest_obj["assets"]
        # # If there are no explicit asset manifest
        # if not raw_asset_manifests:
        #     return [
        #         self.asset_manifest_class(
        #             invocation_target_manifest=self,
        #             asset_manifest_obj=self.full_manifest_obj,
        #             group_name=self._group_name,
        #         )
        #     ]

        asset_manifests = []
        for asset_name, raw_asset_manifest in raw_asset_manifests.items():
            asset_manifests.append(
                self.asset_manifest_class(
                    invocation_target_manifest=self,
                    asset_manifest_obj=raw_asset_manifest,
                    group_name=self._group_name,
                    asset_key_parts=asset_name.split("."),
                )
            )
        return asset_manifests

    # @property
    # def file_name_parts(self) -> List[str]:
    #     return self.full_manifest_path.stem.split(".")

    @property
    def op_name(self) -> str:
        return self._op_name

    @property
    def tags(self) -> dict:
        return {}

    @property
    def asset_specs(self) -> Sequence[AssetSpec]:
        return [asset_manifest.asset_spec for asset_manifest in self.asset_manifests]

    @property
    def metadata(self) -> dict:
        return {}


def resources_without_io_manager(context: AssetExecutionContext):
    original_resources = context.resources.original_resource_dict
    return {k: v for k, v in original_resources.items() if k != "io_manager"}


class NopeInvocationTarget:
    def __init__(self, target_manifest: NopeInvocationTargetManifest):
        self._target_manifest = target_manifest

    @property
    def required_resource_keys(self) -> Set[str]:
        # calling inner property to cache property while
        # still allowing a user to override this
        return self._cached_required_resource_keys

    @cached_property
    def _cached_required_resource_keys(self) -> Set[str]:
        invoke_method = getattr(self, "invoke")
        parameters = inspect.signature(invoke_method).parameters
        return {param for param in parameters if param != "context"}

    @property
    def target_manifest(self) -> NopeInvocationTargetManifest:
        return self._target_manifest

    def to_assets_def(self) -> AssetsDefinition:
        @multi_asset(
            specs=self.target_manifest.asset_specs,
            name=self.target_manifest.op_name,
            op_tags=self.target_manifest.tags,
            required_resource_keys=self.required_resource_keys,
        )
        def _nope_multi_asset(context: AssetExecutionContext):
            return self.invoke(context=context, **resources_without_io_manager(context))

        return _nope_multi_asset

    # Resources as kwargs. Must match set in required_resource_keys.
    # Can return anything that the multi_asset decorator can accept, hence typed as Any
    @abstractmethod
    def invoke(self, context: AssetExecutionContext, **kwargs) -> Any: ...

    @classmethod
    def asset_manifest_class(cls) -> Type:
        if hasattr(cls, "AssetManifest"):
            manifest_cls = getattr(cls, "AssetManifest")
            check.invariant(
                is_subclass(manifest_cls, NopeAssetManifest),
                "User-defined AssetManifest class must subclass NopeAssetManifest",
            )
            return manifest_cls

        return NopeAssetManifest

    @classmethod
    def invocation_target_manifest_class(cls) -> Type:
        if hasattr(cls, "InvocationTargetManifest"):
            invocation_target_manifest = getattr(cls, "InvocationTargetManifest")
            check.invariant(
                is_subclass(invocation_target_manifest, NopeInvocationTargetManifest),
                "User-defined InvocationTargetManifest class must subclass NopeInvocationTargetManifest",
            )
            return invocation_target_manifest
        return NopeInvocationTargetManifest


# Nope doesn't support IO managers, so just provide a noop one so we don't run into annoyances
# like the default IO manager not supporting partitioning out of the box
class NoopIOManager(IOManager):
    def handle_output(self, context, obj) -> None: ...

    def load_input(self, context) -> None:
        return None


class NopeProject:
    @classmethod
    def invocation_target_map(cls) -> dict:
        from dagster._nope.subprocess import NopeSubprocessInvocationTarget

        return {"subprocess": NopeSubprocessInvocationTarget}

    @classmethod
    def make_assets_defs(cls, defs_path: Path) -> Sequence[AssetsDefinition]:
        assets_defs = []
        for group_folder in defs_path.iterdir():
            if not group_folder.is_dir():
                continue

            yaml_files = {}
            # python_files = {}
            for full_path in group_folder.iterdir():
                if full_path.suffix == ".yaml":
                    yaml_files[full_path.stem] = full_path

            for stem_name in set(yaml_files):
                assets_defs.append(
                    cls.make_assets_def(
                        group_name=group_folder.name,
                        full_yaml_path=yaml_files[stem_name],
                    )
                )

        return assets_defs

    @classmethod
    def make_definitions(
        cls, defs_path: Union[str, Path], resources: Optional[Mapping[str, Any]] = None
    ) -> "Definitions":
        from dagster._core.definitions.definitions_class import Definitions

        # TODO. When we add support for more default invocation targets, make
        # an initial pass across the manifests to see what resources we actually
        # need to create

        return Definitions(
            assets=cls.make_assets_defs(
                defs_path=defs_path if isinstance(defs_path, Path) else Path(defs_path)
            ),
            resources={
                **{"io_manager": NoopIOManager()},  # Nope doesn't support IO managers
                **(resources or {"subprocess_client": PipesSubprocessClient()}),
            },
        )

    @classmethod
    def make_assets_def(cls, group_name: str, full_yaml_path: Path) -> AssetsDefinition:
        full_manifest = yaml.load(full_yaml_path.read_text(), Loader=Loader)
        check.invariant(
            full_manifest and "target" in full_manifest,
            f"Invalid manifest file {full_yaml_path}. Must have top-level target key",
        )

        target_map = cls.invocation_target_map()
        target_cls = target_map[full_manifest["target"]]
        script_instance = target_cls(
            target_cls.invocation_target_manifest_class().from_opinionated_layout_path(
                group_name=group_name,
                manifest_path=full_yaml_path,
                asset_manifest_class=target_cls.asset_manifest_class(),
            )
        )
        return script_instance.to_assets_def()
