from collections.abc import Sequence
from typing import cast

import dagster as dg
import dagster._check as check
import pytest
from dagster import AssetsDefinition
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.automation_condition_sensor_definition import (
    DEFAULT_AUTOMATION_CONDITION_SENSOR_NAME,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.reconstruct import ReconstructableRepository
from dagster._core.definitions.repository_definition import RepositoryLoadData
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.definitions import lazy_repository

from dagster_tests.general_tests.test_repository import (
    define_empty_job,
    define_simple_job,
    define_with_resources_job,
)


def define_cacheable_and_uncacheable_assets():
    class MyCacheableAssets(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={"upstream": dg.AssetKey("upstream")},
                    keys_by_output_name={"result": dg.AssetKey(self.unique_id)},
                )
            ]

        def build_definitions(self, data):
            @dg.op(name=self.unique_id)
            def _op(upstream):
                return upstream + 1

            return [
                AssetsDefinition.from_op(
                    _op,
                    keys_by_input_name=cd.keys_by_input_name,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    @dg.asset
    def upstream():
        return 1

    @dg.asset
    def downstream(a, b):
        return a + b

    return [MyCacheableAssets("a"), MyCacheableAssets("b"), upstream, downstream]


@lazy_repository
def cacheable_asset_repo():
    @dg.repository
    def cacheable_asset_repo():
        return [
            define_empty_job(),
            define_simple_job(),
            *define_with_resources_job(),
            define_cacheable_and_uncacheable_assets(),
            dg.define_asset_job(
                "all_asset_job",
                selection=AssetSelection.assets(
                    dg.AssetKey("a"),
                    dg.AssetKey("b"),
                    dg.AssetKey("upstream"),
                    dg.AssetKey("downstream"),
                ),
            ),
        ]

    return cacheable_asset_repo


def test_resolve_empty():
    recon_repo = ReconstructableRepository.for_file(__file__, "cacheable_asset_repo")
    repo = recon_repo.get_definition()
    assert isinstance(repo, dg.RepositoryDefinition)
    assert isinstance(repo.get_job("simple_job"), dg.JobDefinition)
    assert isinstance(repo.get_job("all_asset_job"), dg.JobDefinition)


def test_resolve_missing_key():
    recon_repo = ReconstructableRepository.for_file(
        __file__, "cacheable_asset_repo"
    ).with_repository_load_data(
        RepositoryLoadData(
            cacheable_asset_data={
                "a": [
                    AssetsDefinitionCacheableData(
                        keys_by_input_name={"upstream": dg.AssetKey("upstream")},
                        keys_by_output_name={"result": dg.AssetKey("a")},
                    )
                ]
            }
        ),
    )
    with pytest.raises(check.CheckError, match="No metadata found"):
        recon_repo.get_definition()


def test_resolve_wrong_data():
    recon_repo = ReconstructableRepository.for_file(
        __file__, "cacheable_asset_repo"
    ).with_repository_load_data(
        RepositoryLoadData(
            cacheable_asset_data={
                "a": [
                    AssetsDefinitionCacheableData(
                        keys_by_input_name={"upstream": dg.AssetKey("upstream")},
                        keys_by_output_name={"result": dg.AssetKey("a")},
                    )
                ],
                "b": [
                    AssetsDefinitionCacheableData(
                        keys_by_input_name={"upstream": dg.AssetKey("upstream")},
                        keys_by_output_name={"result": dg.AssetKey("BAD_ASSET_KEY")},
                    )
                ],
            }
        ),
    )
    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"b\".* is not produced by any of the provided asset ops and is not one"
            r" of the provided sources"
        ),
    ):
        recon_repo.get_definition()


def define_uncacheable_and_resource_dependent_cacheable_assets() -> Sequence[
    CacheableAssetsDefinition | dg.AssetsDefinition
]:
    class ResourceDependentCacheableAsset(CacheableAssetsDefinition):
        def __init__(self):
            super().__init__("res_midstream")

        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={"res_upstream": dg.AssetKey("res_upstream")},
                    keys_by_output_name={"result": dg.AssetKey("res_midstream")},
                )
            ]

        def build_definitions(self, data):
            @dg.op(name="res_midstream", required_resource_keys={"foo"})
            def _op(context, res_upstream):
                return res_upstream + context.resources.foo

            return [
                AssetsDefinition.from_op(
                    _op,
                    keys_by_input_name=cd.keys_by_input_name,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    @dg.asset
    def res_upstream(context):
        return context.resources.foo

    @dg.asset
    def res_downstream(context, res_midstream):
        return res_midstream + context.resources.foo

    return [ResourceDependentCacheableAsset(), res_upstream, res_downstream]


def test_resolve_no_resources():
    """Test that loading a repo with a resource-dependent cacheable asset fails if the resource is not
    provided.
    """
    with scoped_definitions_load_context():
        with pytest.raises(dg.DagsterInvalidDefinitionError):
            try:

                @dg.repository
                def resource_dependent_repo_no_resources():
                    return [
                        define_uncacheable_and_resource_dependent_cacheable_assets(),
                        dg.define_asset_job(
                            "all_asset_job",
                        ),
                    ]

                resource_dependent_repo_no_resources.get_all_jobs()
            except dg.DagsterInvalidDefinitionError as e:
                # Make sure we get an error for the cacheable asset in particular
                assert "res_midstream" in str(e)
                raise e


def test_resolve_with_resources():
    """Test that loading a repo with a resource-dependent cacheable asset succeeds if the resource is
    provided.
    """
    with scoped_definitions_load_context():

        @dg.resource
        def foo_resource():
            return 3

        cacheable_assets = define_uncacheable_and_resource_dependent_cacheable_assets()
        cacheable_assets_with_resources = dg.with_resources(
            define_uncacheable_and_resource_dependent_cacheable_assets(),
            {"foo": foo_resource},
        )

        assert (
            cacheable_assets_with_resources[0].unique_id
            == f"{cacheable_assets[0].unique_id}_with_resources"
        )

        @dg.repository
        def resource_dependent_repo_with_resources():
            return [
                cacheable_assets_with_resources,
                dg.define_asset_job(
                    "all_asset_job",
                ),
            ]

        assert isinstance(resource_dependent_repo_with_resources, dg.RepositoryDefinition)
        assert isinstance(
            resource_dependent_repo_with_resources.get_job("all_asset_job"), dg.JobDefinition
        )


def test_group_cached_assets():
    """Test that with_attributes works properly on cacheable assets."""

    class MyCacheableAssets(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={},
                    keys_by_output_name={"result": dg.AssetKey(self.unique_id)},
                )
            ]

        def build_definitions(self, data):
            @dg.op(name=self.unique_id)
            def _op():
                return 5

            return [
                AssetsDefinition.from_op(
                    _op,
                    keys_by_input_name=cd.keys_by_input_name,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    my_cacheable_assets_cool = MyCacheableAssets("foo").with_attributes(
        group_names_by_key={dg.AssetKey("foo"): "my_cool_group"}
    )

    my_lame_group_sel = AssetSelection.groups("my_lame_group")
    assert (
        len(
            my_lame_group_sel.resolve(
                my_cacheable_assets_cool.build_definitions(
                    my_cacheable_assets_cool.compute_cacheable_data()
                )
            )
        )
        == 0
    )

    my_cool_group_sel = AssetSelection.groups("my_cool_group")
    assert (
        len(
            my_cool_group_sel.resolve(
                my_cacheable_assets_cool.build_definitions(
                    my_cacheable_assets_cool.compute_cacheable_data()
                )
            )
        )
        == 1
    )


def test_multiple_wrapped_cached_assets() -> None:
    """Test that multiple wrappers (with_attributes, with_resources) work properly on cacheable assets."""

    @dg.resource
    def foo_resource():
        return 3

    my_cacheable_assets_with_group_and_asset = [
        x.with_attributes(
            asset_key_replacements={
                dg.AssetKey("res_downstream"): dg.AssetKey("res_downstream_too")
            }
        )
        for x in dg.with_resources(
            [
                x.with_attributes(
                    group_names_by_key={dg.AssetKey("res_midstream"): "my_cool_group"}
                )
                for x in define_uncacheable_and_resource_dependent_cacheable_assets()
            ],
            {"foo": foo_resource},
        )
    ]

    with scoped_definitions_load_context():

        @dg.repository
        def resource_dependent_repo_with_resources():
            return [
                my_cacheable_assets_with_group_and_asset,
                dg.define_asset_job(
                    "all_asset_job",
                ),
            ]

        repo = resource_dependent_repo_with_resources
        assert isinstance(repo, dg.RepositoryDefinition)
        assert isinstance(repo.get_job("all_asset_job"), dg.JobDefinition)

        my_cool_group_sel = AssetSelection.groups("my_cool_group")
        cacheable_resource_asset = cast(
            "CacheableAssetsDefinition", my_cacheable_assets_with_group_and_asset[0]
        )
        resolved_defs = list(
            cacheable_resource_asset.build_definitions(
                cacheable_resource_asset.compute_cacheable_data()
            )
        )
        assert (
            len(
                my_cool_group_sel.resolve(
                    resolved_defs
                    + cast("list[AssetsDefinition]", my_cacheable_assets_with_group_and_asset[1:])
                )
            )
            == 1
        )


def test_automation_condition_sensor_definition() -> None:
    class AutomationConditionCacheableAsset(CacheableAssetsDefinition):
        def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
            return [AssetsDefinitionCacheableData(group_name="cacheable")]

        def build_definitions(self, data) -> Sequence[dg.AssetsDefinition]:
            @dg.asset(
                name=self.unique_id,
                automation_condition=AutomationCondition.eager() if self.unique_id == "x" else None,
                group_name=data[0].group_name,
            )
            def _asset() -> None: ...

            return [_asset]

    # will have a default automation condition sensor
    with scoped_definitions_load_context():
        defs = dg.Definitions(assets=[AutomationConditionCacheableAsset("x")])
        default_sensor = defs.resolve_sensor_def(DEFAULT_AUTOMATION_CONDITION_SENSOR_NAME)
        assert default_sensor.asset_selection == AssetSelection.all()
        assert len(defs.get_repository_def().sensor_defs) == 1

    with scoped_definitions_load_context():
        # will not have a default automation condition sensor
        defs = dg.Definitions(assets=[AutomationConditionCacheableAsset("y")])
        assert len(defs.get_repository_def().sensor_defs) == 0

    with scoped_definitions_load_context():

        @dg.repository
        def repo() -> Sequence:
            return [AutomationConditionCacheableAsset("x")]

        assert isinstance(repo, dg.RepositoryDefinition)
        assert len(repo.sensor_defs) == 1
        assert repo.sensor_defs[0].name == DEFAULT_AUTOMATION_CONDITION_SENSOR_NAME
