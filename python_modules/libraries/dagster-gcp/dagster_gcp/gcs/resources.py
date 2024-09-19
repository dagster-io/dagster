from typing import Any, Optional

from dagster import ConfigurableResource, IAttachDifferentObjectToOpContext, resource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from google.cloud import storage
from pydantic import Field

from dagster_gcp.gcs.file_manager import GCSFileManager


class GCSResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """Resource for interacting with Google Cloud Storage.

    Example:
        .. code-block::

            @asset
            def my_asset(gcs: GCSResource):
                with gcs.get_client() as client:
                    # client is a google.cloud.storage.Client
                    ...
    """

    project: Optional[str] = Field(default=None, description="Project name")

    def get_client(self) -> storage.Client:
        """Creates a GCS Client.

        Returns: google.cloud.storage.Client
        """
        return _gcs_client_from_config(project=self.project)

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(
    config_schema=GCSResource.to_config_schema(),
    description="This resource provides a GCS client",
)
def gcs_resource(init_context) -> storage.Client:
    return GCSResource.from_resource_context(init_context).get_client()


class GCSFileManagerResource(ConfigurableResource, IAttachDifferentObjectToOpContext):
    """FileManager that provides abstract access to GCS."""

    project: Optional[str] = Field(default=None, description="Project name")
    gcs_bucket: str = Field(description="GCS bucket to store files")
    gcs_prefix: str = Field(default="dagster", description="Prefix to add to all file paths")

    def get_client(self) -> GCSFileManager:
        """Creates a :py:class:`~dagster_gcp.GCSFileManager` object that implements the
        :py:class:`~dagster._core.storage.file_manager.FileManager` API .

        Returns: GCSFileManager
        """
        gcs_client = _gcs_client_from_config(project=self.project)
        return GCSFileManager(
            client=gcs_client,
            gcs_bucket=self.gcs_bucket,
            gcs_base_key=self.gcs_prefix,
        )

    def get_object_to_set_on_execution_context(self) -> Any:
        return self.get_client()


@dagster_maintained_resource
@resource(config_schema=GCSFileManagerResource.to_config_schema())
def gcs_file_manager(context):
    """FileManager that provides abstract access to GCS.

    Implements the :py:class:`~dagster._core.storage.file_manager.FileManager` API.
    """
    return GCSFileManagerResource.from_resource_context(context).get_client()


def _gcs_client_from_config(project: Optional[str]) -> storage.Client:
    """Creates a GCS Client.

    Args:
        project: The GCP project

    Returns: A GCS client.
    """
    return storage.client.Client(project=project)
