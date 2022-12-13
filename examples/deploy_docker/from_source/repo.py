from dagster_docker import docker_executor

from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)

from dagster import (
    fs_io_manager,
    asset,
    op,
    AssetsDefinition,
    AssetKey,
    DagsterInstance,
    with_resources,
    repository,
)


class MyCacheableAssetsDefinition(CacheableAssetsDefinition):
    _cacheable_data = AssetsDefinitionCacheableData(keys_by_output_name={"result": AssetKey("bar")})

    def compute_cacheable_data(self):
        # used for tracking how many times this function gets called over an execution
        # if this gets called within the step worker, there will be an error as DAGSTER_HOME is not
        # set in those containers
        print("!!!!HERE")
        import time

        time.sleep(15)
        # a quirk of how we end up launching this run requires us to get the definition twice before
        # the run starts
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


@asset
def baz(bar):
    return bar + 1


@repository(default_executor_def=docker_executor)
def deploy_docker_repository():
    return with_resources(
        [foo, MyCacheableAssetsDefinition("bar"), baz],
        resource_defs={
            "io_manager": fs_io_manager.configured({"base_dir": "/tmp/io_manager_storage"})
        },
    )
