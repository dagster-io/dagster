from functools import wraps
from typing import List, Optional

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
)

from .asset import Asset
from .queryable_asset_set import QueryableAssetSet


class Lakehouse:
    """A Lakehouse is a scheme for storing and retrieving assets across heterogeneous compute and
    heterogeneous storage.

    It combines a set of storages, e.g. databases or file systems, with "policies" for
    writing and reading different in-memory types to and from them.

    Lakehouses are used to generate pipelines that update sets of assets in these storages.

    Example:

        .. code-block:: python

            class LocalFileSystemStorage():
                def __init__(self, root):
                    self.root = root

                def get_fs_path(path: Tuple[str, ...]) -> str:
                    return '/'.join((self.root,) + path)

            @resource(config_schema={'root': str})
            def local_file_system_storage(init_context):
                return LocalFileSystemStorage(init_context.resource_config)

            class DataFrameLocalFileSystemPolicy(TypeStoragePolicy):
                @classmethod
                def in_memory_type(cls):
                    return DataFrame

                @classmethod
                def storage_definition(cls):
                    return local_file_system_storage

                @classmethod
                def save(cls, obj, storage, path, _resources):
                    obj.to_csv(storage.get_fs_path(path))

                @classmethod
                def load(cls, storage, path, _resources):
                    return pandas.read_csv(storage.get_fs_path(path))

            mode_def = ModeDefinition(
                name='default', resource_defs={'filesystem': local_file_system_storage}
            )

            preset_def = PresetDefinition(
                name='default',
                mode='default',
                run_config={'resources': {'filesystem': {'config': {'root': '.'}}}},
                solid_selection=None,
            )

            lakehouse = Lakehouse(
                mode_defs=[mode_def],
                preset_defs=[preset_def],
                type_storage_policies=[DataFrameLocalFileSystemPolicy],
            )
    """

    def __init__(
        self, preset_defs=None, mode_defs=None, in_memory_type_resource_keys=None, assets=None
    ):
        """
        Args:
            preset_defs (List[PresetDefinition]): Each preset gives the config necessary to
                instantiate one of the modes.
            mode_defs (List[ModeDefinition]): Each mode defines a mapping of storage keys to storage
                definitions (as resource keys and resource definitions).
            in_memory_type_resource_keys (Dict[type, List[str]]): For any type, declares resource
                keys that need to be around when that type is an input or output of an asset
                derivation, e.g. "pyspark" for asset whose derivation involves PySpark DataFrames.
            assets (List[Asset]): The assets in the house.
        """
        self._preset_defs = preset_defs
        self._mode_defs = mode_defs
        self._in_memory_type_resource_keys = in_memory_type_resource_keys or {}
        self._assets = QueryableAssetSet(assets or [])

    def build_pipeline_definition(self, name, assets_to_update):
        solid_defs = {}
        for asset in assets_to_update:
            if asset.computation:
                solid_defs[asset.path] = self.get_computed_asset_solid_def(asset, assets_to_update)
            else:
                check.failed("All elements of assets_to_update must have computations")

        solid_deps = {
            solid_defs[asset.path].name: {
                solid_defs[dep.asset.path].name: DependencyDefinition(
                    solid_defs[dep.asset.path].name
                )
                for dep in asset.computation.deps.values()
                if dep.asset in assets_to_update
            }
            for asset in assets_to_update
            if asset.computation
        }

        return PipelineDefinition(
            name=name,
            solid_defs=list(solid_defs.values()),
            mode_defs=self._mode_defs,
            dependencies=solid_deps,
            preset_defs=self._preset_defs,
        )

    def get_computed_asset_solid_def(self, computed_asset, assets_in_pipeline):
        output_dagster_type = computed_asset.dagster_type
        output_def = OutputDefinition(output_dagster_type)
        input_defs = []
        deps = computed_asset.computation.deps
        for dep in deps.values():
            if dep.asset in assets_in_pipeline:
                input_dagster_type = dep.asset.dagster_type
                input_def = InputDefinition(
                    name="__".join(dep.asset.path), dagster_type=input_dagster_type
                )
                input_defs.append(input_def)

        required_resource_keys = set(
            [
                resource_key
                for in_memory_type in [dep.in_memory_type for dep in deps.values()]
                + [computed_asset.computation.output_in_memory_type]
                for resource_key in self._in_memory_type_resource_keys.get(in_memory_type, [])
            ]
            + [computed_asset.storage_key]
            + [dep.asset.storage_key for dep in deps.values()]
        )

        return SolidDefinition(
            name="__".join(computed_asset.path),
            input_defs=input_defs,
            compute_fn=self._create_asset_solid_compute_wrapper(
                computed_asset, input_defs, output_def
            ),
            output_defs=[output_def],
            config_schema=None,
            required_resource_keys=required_resource_keys,
            positional_inputs=None,
            version=computed_asset.computation.version,
        )

    def _create_asset_solid_compute_wrapper(self, asset, input_defs, output_def):
        check.inst_param(asset, "asset", Asset)
        check.list_param(input_defs, "input_defs", of_type=InputDefinition)
        check.inst_param(output_def, "output_def", OutputDefinition)

        @wraps(asset.computation.compute_fn)
        def compute(context, _input_defs):
            kwargs = {}

            for arg_name, dep in asset.computation.deps.items():
                storage_key = dep.asset.storage_key
                input_storage = getattr(context.resources, storage_key)
                kwargs[arg_name] = input_storage.load(
                    dep.in_memory_type, dep.asset.path, context.resources
                )
            result = asset.computation.compute_fn(**kwargs)

            output_storage = getattr(context.resources, asset.storage_key)
            output_storage.save(result, asset.path, context.resources)
            yield Output(value=asset.path, output_name=output_def.name)

        return compute

    def query_assets(self, query: Optional[str]) -> List[Asset]:
        """Returns all assets in the Lakehouse that match the query.  The supported query syntax is
        described in detail at https://docs.dagster.io/overview/solid-selection.
        """
        return self._assets.query_assets(query)
