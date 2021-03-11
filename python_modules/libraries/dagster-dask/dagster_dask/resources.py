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
    res = DaskResource(context)

    yield res

    res.close()
