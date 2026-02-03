from typing import Any, Optional

import dagster as dg
from dagster._annotations import beta, preview, public
from pydantic import Field

from dagster_gcp.dataproc.resources import DataprocResource


@public
@beta
@preview
class DataprocResourceComponent(dg.Component, dg.Resolvable, dg.Model):
    """A component that provides a DataprocResource."""

    project_id: str = Field(
        description=(
            "Required. Project ID for the project which the client acts on behalf of. Will be"
            " passed when creating a dataset/job."
        ),
    )

    region: str = Field(
        description="Required. The GCP region.",
    )

    cluster_name: str = Field(
        description=(
            "Required. The cluster name. Cluster names within a project must be unique. Names of"
            " deleted clusters can be reused."
        ),
    )

    labels: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Optional. The labels to associate with this cluster. Label keys must"
            " contain 1 to 63 characters, and must conform to RFC 1035"
            " (https://www.ietf.org/rfc/rfc1035.txt). Label values may be empty, but, if"
            " present, must contain 1 to 63 characters, and must conform to RFC 1035"
            " (https://www.ietf.org/rfc/rfc1035.txt). No more than 32 labels can be associated"
            " with a cluster."
        ),
    )

    cluster_config_yaml_path: Optional[str] = Field(
        default=None,
        description=(
            "Full path to a YAML file containing cluster configuration. See"
            " https://cloud.google.com/dataproc/docs/reference/rest/v1/ClusterConfig for"
            " configuration options. Only one of cluster_config_yaml_path,"
            " cluster_config_json_path, or cluster_config_dict may be provided."
        ),
    )

    cluster_config_json_path: Optional[str] = Field(
        default=None,
        description=(
            "Full path to a JSON file containing cluster configuration. See"
            " https://cloud.google.com/dataproc/docs/reference/rest/v1/ClusterConfig for"
            " configuration options. Only one of cluster_config_yaml_path,"
            " cluster_config_json_path, or cluster_config_dict may be provided."
        ),
    )

    cluster_config_dict: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Python dictionary containing cluster configuration. See"
            " https://cloud.google.com/dataproc/docs/reference/rest/v1/ClusterConfig for"
            " configuration options. Only one of cluster_config_yaml_path,"
            " cluster_config_json_path, or cluster_config_dict may be provided."
        ),
    )

    resource_key: Optional[str] = Field(
        default=None,
        description="The key under which the Dataproc resource will be bound to the definitions.",
    )

    @property
    def resource(self) -> DataprocResource:
        """Returns a configured DataprocResource."""
        return DataprocResource(
            project_id=self.project_id,
            region=self.region,
            cluster_name=self.cluster_name,
            labels=self.labels,
            cluster_config_yaml_path=self.cluster_config_yaml_path,
            cluster_config_json_path=self.cluster_config_json_path,
            cluster_config_dict=self.cluster_config_dict,
        )

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        if self.resource_key is None:
            return dg.Definitions()
        return dg.Definitions(resources={self.resource_key: self.resource})
