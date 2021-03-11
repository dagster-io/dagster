from dagster import Bool, Int, String
from dagster import Field, Permissive, Selector, Shape
from dagster import check
from dask.distributed import Client


# Map of the possible Dask cluster types and their associated classes.
# Users must install the modules associated with the cluster types they
# want to use (e.g., dask_cloudprovider for ecs).
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


# Common config schema for specifying a Dask client and/or cluster.
DaskConfigSchema = {
    # The client config fields correspond to the init arguments for the Dask distributed.Client class.
    # https://distributed.dask.org/en/latest/api.html#distributed.Client
    "client": Field(
        Permissive(
            {
                "address": Field(
                    String,
                    description="Address of a Scheduler server. A Cluster object will be passed in if a cluster config is provided.",
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
                    description="Gives the client a name that will be included in logs generated on the scheduler.",
                    is_required=False,
                ),
                "direct_to_workers": Field(
                    Bool,
                    description="Whether or not to connect directly to the workers.",
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

    # The cluster config fields consist of a cluster type keys and permissive dicts of key-values
    # that will be passed in to the corresponding cluster class. Only a single cluster type may be
    # specified at a time.
    "cluster": Field(
        Selector(
            {
                **{
                    key: Field(
                        Permissive(),
                        is_required=False,
                        description=f"{meta['name']} cluster config. Requires {meta['module']}.",
                    )
                    for key, meta in DaskClusterTypes.items()
                },
                **{
                    "existing": Field(
                        {"address": StringSource},
                        description="Connect to an existing scheduler (deprecated, use client address config).",
                    )
                },
            }
        ),
        description="Create a Dask cluster. Will be passed as the client address.",
        is_required=False,
    ),
}


def create_from_config(config):
    """Create Dask Client and Cluster objects based on the provided config, which may be
    an executor_config or resource_config.
    """

    cluster_config = check.opt_nullable_dict_param(config.get("cluster"), "cluster")
    client_config = check.opt_dict_param(config.get("client"), "client")

    # Construct a cluster object.
    if cluster_config:
        # Unpack the cluster type and init options. The cluster_config should consist
        # of a single dict member because the `cluster` field is defined as a selector.
        cluster_type, cluster_opts = next(iter(cluster_config.items()))

        # Deprecated option for specifying an existing cluster by its scheduler address.
        if cluster_type == "existing":
            client_config["address"] = cluster_opts["address"]

        # Get the module and class information from DaskClusterTypes, and instantiate
        # the cluster object.
        else:
            cluster_meta = DaskClusterType.get(cluster_type, None)
            if not cluster_meta:
                raise ValueError(f'Unknown cluster type "{cluster_type}".')

            # Dynamically import the cluster module and get the cluster class.
            from importlib import import_module

            cluster_module = import_module(cluster_meta["module"])
            cluster_class = getattr(cluster_module, cluster_meta["class"])

            cluster = cluster_class(**cluster_opts)
            client_config["address"] = cluster
    else:
        cluster = None

    # Construct a client object. If a cluster was created above, set the cluster object
    # as the `address` parameter. If no address or cluster object is provided, Dask
    # will implicitly create a LocalCluster object.
    client = Client(**client_config)

    return client, cluster
