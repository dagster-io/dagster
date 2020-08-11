from dagster import (
    # Definition
    Field,

    # Decorators
    resource,

    # Config
    Permissive,
    Selector,
)
from distributed import Client


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
    }.items()
}


class DaskResource(object):
    def __init__(self, context):
        config_type, config_opts = next(iter(context.resource_config.items()))

        if "scheduler" == config_type:
            self._cluster = None
            self._client = Client(**config_opts, set_as_default=False)
        elif "cluster" == config_type:
            from importlib import import_module

            cluster_type, cluster_opts = next(iter(config_opts.items()))
            cluster_meta = DaskClusterTypes.get(cluster_type, None)
            if not cluster_meta:
                raise ValueError(f"Unknown cluster type “{cluster_type}”.")

            cluster_module = import_module(cluster_meta["module"])
            cluster_class = getattr(cluster_module, cluster_meta["class"])

            self._cluster = cluster_class(**cluster_opts)
            self._client = Client(self._cluster, set_as_default=False)

    @property
    def cluster(self):
        return self._cluster
    
    @property
    def client(self):
        return self._client


@resource(
    description="Dask Client resource.",
    config_schema=Selector({
        "scheduler": Field({
            "address": Field(str, description="Address of a Scheduler server."),
            "timeout": Field(int, description="Timeout duration for initial connection to the scheduler.", is_required=False),
            "name": Field(str, description="Name of client that will be included in logs generated on the scheduler.", is_required=False),
            "direct_to_workers": Field(bool, description="Whether to connect directly to the workers.", is_required=False),
            "heartbeat_interval": Field(int, description="Time in milliseconds between heartbeats to scheduler.", is_required=False),
        }, description="Connect to a Dask scheduler."),
        "cluster": Field({
            key: Field(Permissive(), is_required=False, description=f"{meta['name']} cluster configuration.")
            for key, meta in DaskClusterTypes.items()
        }, description="Create a Dask cluster."),
    })
)
def dask_resource(context):
    return DaskResource(context)
