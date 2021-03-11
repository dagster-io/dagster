from dagster import Bool, Int, String
from dagster import Field, Permissive, Selector, Shape


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
