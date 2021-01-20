from dagster import Field, Noneable, StringSource, resource
from dagster.utils.merger import merge_dicts
from google.cloud import storage

from .file_manager import GCSFileManager

GCS_CLIENT_CONFIG = {
    "project": Field(Noneable(StringSource), is_required=False, description="Project name")
}


@resource(
    GCS_CLIENT_CONFIG, description="This resource provides a GCS client",
)
def gcs_resource(init_context):
    return _gcs_client_from_config(init_context.resource_config)


@resource(
    merge_dicts(
        GCS_CLIENT_CONFIG,
        {
            "gcs_bucket": Field(StringSource),
            "gcs_prefix": Field(StringSource, is_required=False, default_value="dagster"),
        },
    )
)
def gcs_file_manager(context):
    """FileManager that provides abstract access to GCS.
    
    Implements the :py:class:`~dagster.core.storage.file_manager.FileManager` API.
    """
    gcs_client = _gcs_client_from_config(context.resource_config)
    return GCSFileManager(
        client=gcs_client,
        gcs_bucket=context.resource_config["gcs_bucket"],
        gcs_base_key=context.resource_config["gcs_prefix"],
    )


def _gcs_client_from_config(config):
    """
    Args:
        config: A configuration containing the fields in GCS_CLIENT_CONFIG.

    Returns: A GCS client.
    """
    project = config.get("project", None)
    return storage.client.Client(project=project)
