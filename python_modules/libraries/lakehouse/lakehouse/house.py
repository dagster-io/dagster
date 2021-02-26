from functools import wraps
from typing import List, Optional

from dagster import (
    AssetMaterialization,
    CompositeSolidDefinition,
    DependencyDefinition,
    InputDefinition,
    Nothing,
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
        solid_defs, solid_deps = self._get_solid_deps_and_defs(assets_to_update)

        return PipelineDefinition(
            name=name,
            solid_defs=list(solid_defs.values()),
            mode_defs=self._mode_defs,
            dependencies=solid_deps,
            preset_defs=self._preset_defs,
        )

    def build_composite_solid_definition(self, name, assets_to_update, include_nothing_input=False):
        """Build a composite solid definition for the assets in `assets_to_update`.

        By default the composite solid will not accept any inputs. If you need to run this composite
        _after_ other solids have run, pass `include_nothing_input=True`, which will create a
        single input of type `Nothing` to the composite solid, and a mapping to each 'source' asset
        input (i.e. those assets without `compute_fn`s, such as those created by `source_asset` or
        `source_table`).

        Examples:

            .. code-block:: python

            @solid(required_resource_keys={"filesystem", "pyspark"})
            def save_orders(context) -> Nothing:
                orders = context.resources.pyspark.spark_session.createDataFrame([
                    Row(id=1, name="foo"), Row(id=2, name="bar"), Row(id=3, name="baz"),
                ])
                path = context.resources.filesystem.get_fs_path(("orders.csv",))
                orders.write.format("csv").options(header="true").save(path, mode="overwrite")

            orders_asset = source_asset(path="orders.csv")

            @computed_asset(input_assets=[orders_asset])
            def orders_top1_asset(orders: DataFrame) -> DataFrame:
                return orders.limit(1)

            run_lakehouse = lakehouse.build_composite_solid_definition(
                name="lakehouse_solid",
                assets_to_update=[orders_top1_asset],
                include_nothing_input=True,
            )

            @pipeline(mode_defs=[mode_def], preset_defs=[preset_def])
            def simple_pipeline():
                run_lakehouse(save_orders())

            # If you have multiple solids which need to run first:

            @lambda_solid
            def other_side_effect() -> Nothing:
                # Perhaps this writes to a database or some other required source table.
                pass

            @lambda_solid(
                input_defs=[InputDefinition("orders", Nothing), InputDefinition("other", Nothing)]
            )
            def wait_until_complete() -> Nothing:
                pass

            @pipeline(mode_defs=[mode_def], preset_defs=[preset_def])
            def pipeline_multi_deps():
                completed = wait_until_complete(orders=save_orders(), other=other_side_effect())
                run_lakehouse(completed)

        """
        solid_defs, solid_deps = self._get_solid_deps_and_defs(
            assets_to_update, include_nothing_input
        )

        if include_nothing_input:
            # Map a single `InputDefinition`, of type `Nothing`, to every
            # solid in the solid definitions we just created that have an input
            # named 'nothing'.
            # Ideally we'd do this based on something more explicit than the names and types
            # of solid inputs, but it's vanishingly unlikely that users will return `Nothing`
            # from an asset, since there would be nothing to save to the Lakehouse that way.
            nothing_input = InputDefinition("nothing", Nothing)
            input_mappings = [
                nothing_input.mapping_to("__".join(solid_name), "nothing")
                for solid_name, solid_def in solid_defs.items()
                if solid_def.input_defs[0].name == "nothing"
                and solid_def.input_defs[0].dagster_type.is_nothing
            ]
        else:
            input_mappings = None

        return CompositeSolidDefinition(
            name=name,
            solid_defs=list(solid_defs.values()),
            dependencies=solid_deps,
            input_mappings=input_mappings,
        )

    def _get_solid_deps_and_defs(self, assets_to_update, include_nothing_input=False):
        solid_defs = {}
        for asset in assets_to_update:
            if asset.computation:
                solid_defs[asset.path] = self.get_computed_asset_solid_def(
                    asset, assets_to_update, include_nothing_input
                )
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
        return solid_defs, solid_deps

    def get_computed_asset_solid_def(
        self, computed_asset, assets_in_pipeline, include_nothing_input=False
    ):
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

        # Add a `Nothing` input if requested and if this asset has no input definitions.
        if include_nothing_input and not input_defs:
            input_defs.append(InputDefinition(name="nothing", dagster_type=Nothing))

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
            yield AssetMaterialization(
                asset_key=asset.key,
            )
            yield Output(value=asset.path, output_name=output_def.name)

        return compute

    def query_assets(self, query: Optional[str]) -> List[Asset]:
        """Returns all assets in the Lakehouse that match the query.  The supported query syntax is
        described in detail at https://docs.dagster.io/overview/solid-selection.
        """
        return self._assets.query_assets(query)
