from dagster import resource

from .config import DaskConfigSchema, create_from_config


class DaskResource:
    def __init__(self, context):
        self._client, self._cluster = create_from_config(context.resource_config)

    @property
    def cluster(self):
        return self._cluster

    @property
    def client(self):
        return self._client

    def close(self):
        self.client.close()
        if self.cluster:
            self.cluster.close()

        self._client, self._cluster = None, None


@resource(
    description="Dask Client resource.",
    config_schema=DaskConfigSchema,
)
def dask_resource(context):
    """Resource for a Dask cluster.

    The Dask resource gives solids access a Dask cluster for computations. This is different
    from the Dask executor, which runs an entire Dagster pipeline as a graph of futures on
    Dask.

    The resource provides two properties for accessing configured ``cluster`` and ``client``
    objects. Typically there is no need to interact with these directly. Simply declaring a
    Dask resource will make its client the current Dask client when running a pipeline. Solids
    can work with Dask DataFrames and other objects as normal.
    """
    res = DaskResource(context)

    yield res

    res.close()
