from dagster import resource
from dask.distributed import Client

from .config import DaskConfigSchema


class DaskResource:
    def __init__(self, context):
        # Create a Dask cluster if a cluster config is specified.
        # This will be passed as the address value to the Client.
        cluster_config = context.resource_config.get("cluster", None)
        if cluster_config:
            from importlib import import_module

            cluster_type, cluster_opts = next(iter(cluster_config.items()))
            cluster_meta = DaskClusterTypes.get(cluster_type, None)
            if not cluster_meta:
                raise ValueError(f"Unknown cluster type “{cluster_type}”.")

            # Import the cluster module by name, and get the cluster Class.
            cluster_module = import_module(cluster_meta["module"])
            cluster_class = getattr(cluster_module, cluster_meta["class"])

            self._cluster = cluster_class(**cluster_opts)
        else:
            self._cluster = None

        # Get the client config, and set `address` to a cluster obejct
        # if one was created above. Then, instantiate a Client object.
        client_config = dict(context.resource_config.get("client", {}))
        if self.cluster:
            client_config["address"] = self.cluster
        self._client = Client(**client_config)

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
