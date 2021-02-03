from dagster import Bool, Field, Int, Permissive, Selector, Shape, String, resource
from dask.distributed import Client

DaskClusterTypes = {
    key: dict(zip(("name", "module", "class"), values))
    for key, values in {
        "local": ("Local", "dask.distributed", "LocalCluster"),
        "yarn": ("YARN", "dask_yarn", "YarnCluster"),
        "ssh": ("SSH", "dask.distributed", "SSHCluster"),
        "pbs": ("PBS", "dask_jobqueue", "PBSCluster"),
        "moab": ("Moab", "dask_jobqueue", "MoabCluster"),
        "sge": ("SGE", "dask_jobqueue", "SGECluster"),
        "lsf": ("LSF", "dask_jobqueue", "LSFCluster"),
        "slurm": ("SLURM", "dask_jobqueue", "SLURMCluster"),
        "oar": ("OAR", "dask_jobqueue", "OARCluster"),
        "kube": ("Kubernetes", "dask_kubernetes", "KubeCluster"),
        "azureml": ("Azure ML", "dask_cloudprovider", "AzureMLCluster"),
        "ecs": ("AWS ECS", "dask_cloudprovider", "ECSCluster"),
        "fargate": ("AWS ECS on Fargate", "dask_cloudprovider", "FargateCluster"),
    }.items()
}


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
    config_schema=Shape(
        {
            "client": Field(
                Permissive(
                    {
                        "address": Field(
                            String,
                            description="Address of a Scheduler server.",
                            is_required=False,
                        ),
                        "timeout": Field(
                            Int,
                            description="Timeout duration for initial connection to the scheduler.",
                            is_required=False,
                        ),
                        "set_as_default": Field(
                            Bool,
                            description="Claim this scheduler as the global dask scheduler.",
                            is_required=False,
                        ),
                        "scheduler_file": Field(
                            String,
                            description="Path to a file with scheduler information, if available.",
                            is_required=False,
                        ),
                        "security": Field(
                            Bool,
                            description="Optional security information.",
                            is_required=False,
                        ),
                        "asynchronous": Field(
                            Bool,
                            description="Set to True if using this client within async/await functions.",
                            is_required=False,
                        ),
                        "name": Field(
                            String,
                            description="Name of client that will be included in logs generated on the scheduler.",
                            is_required=False,
                        ),
                        "direct_to_workers": Field(
                            Bool,
                            description="Whether to connect directly to the workers.",
                            is_required=False,
                        ),
                        "heartbeat_interval": Field(
                            Int,
                            description="Time in milliseconds between heartbeats to scheduler.",
                            is_required=False,
                        ),
                    }
                ),
                description="Dask distributed client options.",
                is_required=False,
            ),
            "cluster": Field(
                Selector(
                    {
                        key: Field(
                            Permissive(),
                            is_required=False,
                            description=f"{meta['name']} cluster config. Requires {meta['module']}.",
                        )
                        for key, meta in DaskClusterTypes.items()
                    }
                ),
                description="Create a Dask cluster. Will be passed as the client address.",
                is_required=False,
            ),
        }
    ),
)
def dask_resource(context):
    res = DaskResource(context)

    yield res

    res.close()
