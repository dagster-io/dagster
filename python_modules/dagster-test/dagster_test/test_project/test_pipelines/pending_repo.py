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
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cacheable_data = AssetsDefinitionCacheableData(keys_by_output_name={"result": AssetKey("bar")})

    def compute_cacheable_data(self):
        # used for tracking how many times this function gets called over an execution
        # if this gets called within the step worker, there will be an error as DAGSTER_HOME is not
        # set in those containers
        instance = DagsterInstance.get()
        kvs_key = "compute_cacheable_data_called"
        num_called = int(instance.run_storage.kvs_get({kvs_key}).get(kvs_key, "0"))
        # a quirk of how we end up launching this run requires us to get the definition twice before
        # the run starts
        assert num_called < 3
        instance.run_storage.kvs_set({kvs_key: str(num_called + 1)})
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
            define_asset_job("demo_pipeline_docker", executor_def=docker_executor),
        ]

    return demo_execution_repo
