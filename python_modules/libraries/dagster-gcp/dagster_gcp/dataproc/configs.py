from dagster import Field, Permissive, StringSource

from dagster_gcp.dataproc.configs_dataproc_cluster import define_dataproc_cluster_config
from dagster_gcp.dataproc.configs_dataproc_job import define_dataproc_job_config


def define_dataproc_create_cluster_config():
    cluster_name = Field(
        StringSource,
        description="""Required. The cluster name. Cluster names within a project must be unique.
        Names of deleted clusters can be reused.""",
        is_required=True,
    )
    labels = Field(
        Permissive(),
        description="""Optional. The labels to associate with this cluster. Label keys must
        contain 1 to 63 characters, and must conform to RFC 1035
        (https://www.ietf.org/rfc/rfc1035.txt). Label values may be empty, but, if
        present, must contain 1 to 63 characters, and must conform to RFC 1035
        (https://www.ietf.org/rfc/rfc1035.txt). No more than 32 labels can be associated
        with a cluster.""",
        is_required=False,
    )

    return {
        "projectId": _define_project_id_config(),
        "region": _define_region_config(),
        "clusterName": cluster_name,
        "cluster_config": define_dataproc_cluster_config(),
        "labels": labels,
    }


def define_dataproc_submit_job_config():
    return {
        "job": define_dataproc_job_config(),
        "projectId": _define_project_id_config(),
        "region": _define_region_config(),
    }


def _define_project_id_config():
    return Field(
        StringSource,
        description="""Required. Project ID for the project which the client acts on behalf of. Will
        be passed when creating a dataset / job. If not passed, falls back to the default inferred
        from the environment.""",
        is_required=True,
    )


def _define_region_config():
    return Field(StringSource, is_required=True)
