import os

from dagster import (
    AssetKey,
    AssetsDefinition,
    asset,
    define_asset_job,
    op,
    repository,
    with_resources,
)
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cacheable_data = AssetsDefinitionCacheableData(keys_by_output_name={"result": AssetKey("bar")})

    def compute_cacheable_data(self):
        # make sure this never gets called in the normal course of a run
        assert os.getenv("IN_EXTERNAL_PROCESS") == "yes"
        return [self._cacheable_data]

    def build_definitions(self, data):
        assert len(data) == 1
        assert data == [self._cacheable_data]

        @op
        def _op(foo):
            return foo + 1

        return [
            AssetsDefinition.from_op(_op, keys_by_output_name=cd.keys_by_output_name) for cd in data
        ]


@asset
def foo():
    return 1


def define_demo_execution_repo():
    from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
    from dagster_docker import docker_executor

    @repository
    def demo_execution_repo():
        return [
            with_resources([foo], {"s3": s3_resource, "io_manager": s3_pickle_io_manager}),
            MyCacheableAssetsDefinition("xyz"),
            define_asset_job("demo_job_docker", executor_def=docker_executor),
        ]

    return demo_execution_repo
