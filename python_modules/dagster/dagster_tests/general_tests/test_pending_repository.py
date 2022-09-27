import pytest

import dagster._check as check
from dagster import (
    AssetKey,
    AssetSelection,
    AssetsDefinition,
    DagsterInvalidDefinitionError,
    JobDefinition,
    RepositoryDefinition,
    asset,
    define_asset_job,
    op,
    repository,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionMetadata,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.repository_definition import (
    PendingRepositoryDefinition,
    RepositoryMetadata,
)

from .test_repository import define_empty_job, define_simple_job, define_with_resources_job


def define_cacheable_and_uncacheable_assets():
    class MyCacheableAssets(CacheableAssetsDefinition):
        def get_metadata(self):
            return [
                AssetsDefinitionMetadata(
                    keys_by_input_name={"upstream": AssetKey("upstream")},
                    keys_by_output_name={"result": AssetKey(self.unique_id)},
                )
            ]

        def get_definitions(self, metadata):
            @op(name=self.unique_id)
            def _op(upstream):
                return upstream + 1

            return [
                AssetsDefinition.from_op(
                    _op,
                    keys_by_input_name=md.keys_by_input_name,
                    keys_by_output_name=md.keys_by_output_name,
                )
                for md in metadata
            ]

    @asset
    def upstream():
        return 1

    @asset
    def downstream(a, b):
        return a + b

    return [MyCacheableAssets("a"), MyCacheableAssets("b"), upstream, downstream]


@repository
def pending_repo():
    return [
        define_empty_job(),
        define_simple_job(),
        *define_with_resources_job(),
        define_cacheable_and_uncacheable_assets(),
        define_asset_job(
            "all_asset_job",
            selection=AssetSelection.keys(
                AssetKey("a"), AssetKey("b"), AssetKey("upstream"), AssetKey("downstream")
            ),
        ),
    ]


def test_resolve_empty():
    assert isinstance(pending_repo, PendingRepositoryDefinition)
    repo = pending_repo.resolve(repository_metadata=None)
    assert isinstance(repo, RepositoryDefinition)
    assert isinstance(repo.get_job("simple_job"), JobDefinition)
    assert isinstance(repo.get_job("all_asset_job"), JobDefinition)


def test_resolve_missing_key():
    assert isinstance(pending_repo, PendingRepositoryDefinition)
    with pytest.raises(check.CheckError, match="No metadata found"):
        pending_repo.resolve(
            repository_metadata=RepositoryMetadata(
                cached_metadata_by_key={
                    "a": [
                        AssetsDefinitionMetadata(
                            keys_by_input_name={"upstream": AssetKey("upstream")},
                            keys_by_output_name={"result": AssetKey("a")},
                        )
                    ]
                }
            )
        )


def test_resolve_wrong_data():
    assert isinstance(pending_repo, PendingRepositoryDefinition)
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r"Input asset .*\"b\".* is not produced by any of the provided asset ops and is not one of the provided sources",
    ):
        pending_repo.resolve(
            repository_metadata=RepositoryMetadata(
                cached_metadata_by_key={
                    "a": [
                        AssetsDefinitionMetadata(
                            keys_by_input_name={"upstream": AssetKey("upstream")},
                            keys_by_output_name={"result": AssetKey("a")},
                        )
                    ],
                    "b": [
                        AssetsDefinitionMetadata(
                            keys_by_input_name={"upstream": AssetKey("upstream")},
                            keys_by_output_name={"result": AssetKey("BAD_ASSET_KEY")},
                        )
                    ],
                }
            )
        )
