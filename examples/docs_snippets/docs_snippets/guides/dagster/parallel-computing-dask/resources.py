## first_resource_start

from dask.distributed import Client

# isort: skip_file
from dagster import ConfigurableResource


class DaskResource(ConfigurableResource):
    def make_dask_cluster(self) -> Client:
        client = Client()
        return client


## first_resource_end

from dagster import asset


@asset
def asset_1():
    pass


@asset
def asset_2():
    pass


## second_resource_start
from dagster import ConfigurableResource, Definitions
from dask.distributed import Client, LocalCluster


class DaskResource(ConfigurableResource):
    n_workers: int

    def make_dask_cluster(self) -> Client:
        client = Client(LocalCluster(n_workers=self.n_workers))
        return client


defs = Definitions(
    assets=[asset_1, asset_2], resources={"MyDaskResource": DaskResource(n_workers=2)}
)

## second_resource_end


## third_resource_start
class DaskResource(ConfigurableResource):
    def make_dask_cluster(self, n_workers) -> Client:
        client = Client(LocalCluster(n_workers))
        return client


@asset
def resource_asset(MyDaskResource: DaskResource):
    return MyDaskResource.make_dask_cluster(n_workers=5)


## third_resource_end
