from dagster import (
    AssetKey,
    AssetsDefinition,
    DagsterInstance,
    asset,
    define_asset_job,
    op,
    repository,
    with_resources,
)
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition, CachedAssetsData


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cached_data = CachedAssetsData(keys_by_output_name={"result": AssetKey("bar")})

    def get_cached_data(self):
        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "get_cached_data_called"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        print("x" * 1000)
        print(num_called)
        print("x" * 1000)
        # assert num_called == 0
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})
        return [self._cached_data]

    def get_definitions(self, cached_data):
        assert len(cached_data) == 1
        assert cached_data == [self._cached_data]
        # used for tracking how many times this function gets called over an execution
        instance = DagsterInstance.get()
        kvs_key = "get_definitions_called"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})
        print("y" * 1000)
        print(num_called)
        print("y" * 1000)
        # assert num_called < 4

        @op
        def _op(foo):
            return foo + 1

        return [
            AssetsDefinition.from_op(_op, keys_by_output_name=cd.keys_by_output_name)
            for cd in cached_data
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
            define_asset_job("demo_pipeline_docker", executor_def=docker_executor),
        ]

    return demo_execution_repo
