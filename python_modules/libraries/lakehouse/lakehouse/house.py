from abc import ABCMeta, abstractmethod
from functools import wraps

import six

from dagster import (
    DependencyDefinition,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    check,
)

from .asset import ComputedAsset


class Lakehouse:
    '''A Lakehouse is a scheme for storing and retrieving assets across heterogeneous compute and
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

            @resource(config={'root': str})
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
                environment_dict={'resources': {'filesystem': {'config': {'root': '.'}}}},
                solid_selection=None,
            )

            lakehouse = Lakehouse(
                mode_defs=[mode_def],
                preset_defs=[preset_def],
                type_storage_policies=[DataFrameLocalFileSystemPolicy],
            )
    '''

    def __init__(
        self, preset_defs, mode_defs, in_memory_type_resource_keys=None, type_storage_policies=None
    ):
        '''
        Args:
            preset_defs (List[PresetDefinition]): Each preset gives the config necessary to
                instantiate one of the modes.
            mode_defs (List[ModeDefinition]): Each mode defines a mapping of storage keys to storage
                definitions (as resource keys and resource definitions).
            in_memory_type_resource_keys (Dict[type, List[str]]): For any type, declares resource
                keys that need to be around when that type is an input or output of an asset
                derivation, e.g. "pyspark" for asset whose derivation involves PySpark DataFrames.
            type_storage_policies (List[Type[TypeStoragePolicy]]): Each policy describes how to read
                and write a single in-memory type to a single storage definition.
        '''
        self._presets_by_name = {preset.name: preset for preset in preset_defs}
        self._modes_by_name = {mode.name: mode for mode in mode_defs}
        self._in_memory_type_resource_keys = in_memory_type_resource_keys or {}
        self._policies_by_type_storage = {
            (policy.in_memory_type(), policy.storage_definition()): policy
            for policy in type_storage_policies
        }

    def build_pipeline_definition(self, name, assets_to_update):
        solid_defs = {}
        for asset in assets_to_update:
            if isinstance(asset, ComputedAsset):
                for mode in self._modes_by_name.values():
                    self.check_has_policy(mode, asset.output_in_memory_type, asset.storage_key)

                for mode in self._modes_by_name.values():
                    for dep in asset.deps.values():
                        self.check_has_policy(mode, dep.in_memory_type, dep.asset.storage_key)

                solid_defs[asset.path] = self.get_computed_asset_solid_def(asset, assets_to_update)
            else:
                check.failed('All elements of assets_to_update must be ComputedAssets')

        solid_deps = {
            solid_defs[asset.path].name: {
                solid_defs[dep.asset.path].name: DependencyDefinition(
                    solid_defs[dep.asset.path].name
                )
                for dep in asset.deps.values()
                if dep.asset in assets_to_update
            }
            for asset in assets_to_update
            if isinstance(asset, ComputedAsset)
        }

        return PipelineDefinition(
            name=name,
            solid_defs=list(solid_defs.values()),
            mode_defs=list(self._modes_by_name.values()),
            dependencies=solid_deps,
            preset_defs=list(self._presets_by_name.values()),
        )

    def get_computed_asset_solid_def(self, computed_asset, assets_in_pipeline):
        output_dagster_type = computed_asset.dagster_type
        output_def = OutputDefinition(output_dagster_type)
        input_defs = []
        for dep in computed_asset.deps.values():
            if dep.asset in assets_in_pipeline:
                input_dagster_type = dep.asset.dagster_type
                input_def = InputDefinition(
                    name='__'.join(dep.asset.path), dagster_type=input_dagster_type
                )
                input_defs.append(input_def)

        required_resource_keys = set(
            [
                resource_key
                for in_memory_type in [dep.in_memory_type for dep in computed_asset.deps.values()]
                + [computed_asset.output_in_memory_type]
                for resource_key in self._in_memory_type_resource_keys.get(in_memory_type, [])
            ]
            + [computed_asset.storage_key]
            + [dep.asset.storage_key for dep in computed_asset.deps.values()]
        )

        return SolidDefinition(
            name='__'.join(computed_asset.path),
            input_defs=input_defs,
            compute_fn=self._create_asset_solid_compute_wrapper(
                computed_asset, input_defs, output_def
            ),
            output_defs=[output_def],
            config=None,
            required_resource_keys=required_resource_keys,
            positional_inputs=None,
        )

    def _create_asset_solid_compute_wrapper(self, asset, input_defs, output_def):
        check.inst_param(asset, 'asset', ComputedAsset)
        check.list_param(input_defs, 'input_defs', of_type=InputDefinition)
        check.inst_param(output_def, 'output_def', OutputDefinition)

        @wraps(asset.compute_fn)
        def compute(context, _input_defs):
            kwargs = {}
            mode = self._modes_by_name[context.mode_def.name]

            for arg_name, dep in asset.deps.items():
                storage_key = dep.asset.storage_key
                policy = self.policy_for_type_storage(mode, dep.in_memory_type, storage_key)
                storage = getattr(context.resources, storage_key)
                kwargs[arg_name] = policy.load(storage, dep.asset.path, context.resources)

            result = asset.compute_fn(**kwargs)
            output_policy = self.policy_for_type_storage(
                mode, asset.output_in_memory_type, asset.storage_key
            )
            storage = getattr(context.resources, asset.storage_key)
            output_policy.save(result, storage, asset.path, context.resources)
            yield Output(value=asset.path, output_name=output_def.name)

        return compute

    def check_has_policy(self, mode, in_memory_type, storage_key):
        check.invariant(
            storage_key in mode.resource_defs,
            'Mode {name} is missing storage_key {storage_key}'.format(
                name=mode.name, storage_key=storage_key,
            ),
        )
        storage_def = mode.resource_defs[storage_key]
        check.invariant(
            (in_memory_type, storage_def) in self._policies_by_type_storage,
            'Mode {name} is missing TypeStoragePolicy for storage_key {storage_key} '
            'and in-memory type {in_memory_type}'.format(
                name=mode.name, storage_key=storage_key, in_memory_type=in_memory_type,
            ),
        )

    def policy_for_type_storage(self, mode, in_memory_type, storage_key):
        storage_def = mode.resource_defs[storage_key]
        return self._policies_by_type_storage[in_memory_type, storage_def]


class TypeStoragePolicy(six.with_metaclass(ABCMeta)):
    '''A TypeStoragePolicy describes how to save and load a particular in-memory type to
    and from a particular kind of storage, e.g. how to save and load Pandas DataFrames to/from
    CSV files in S3.'''

    @classmethod
    @abstractmethod
    def in_memory_type(cls):
        pass

    @classmethod
    @abstractmethod
    def storage_definition(cls):
        pass

    @classmethod
    @abstractmethod
    def save(cls, obj, storage, path, resources):
        pass

    @classmethod
    @abstractmethod
    def load(cls, storage, path, resources):
        pass
