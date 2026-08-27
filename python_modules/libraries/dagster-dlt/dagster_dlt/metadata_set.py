from collections.abc import Mapping
from typing import Any

from dagster import MetadataValue
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dlt.extract.resource import DltResource


def _config_to_metadata_value(value: Any) -> MetadataValue | None:
    """Coerce a dlt config value that may be a string or a nested mapping.

    Several dlt table settings (e.g. ``schema_contract``) can be expressed either as a simple
    string shorthand or as a nested dict. We render the mapping form as JSON so it is displayed
    in a structured way, and the string form as plain text. Dynamically-computed hints (callables)
    are only resolved during the run, so they are treated as absent at definition time.
    """
    if value is None or callable(value):
        return None
    if isinstance(value, Mapping):
        return MetadataValue.json(dict(value))
    return MetadataValue.text(str(value))


class DagsterDltMetadataSet(NamespacedMetadataSet):
    """Metadata entries that apply to assets loaded by dlt.

    These are sourced directly from the dlt resource's hints so that dlt's own configuration is
    surfaced on the asset at definition time rather than re-derived by Dagster.

    Args:
        write_disposition (Optional[MetadataValue]): How dlt writes the table, e.g. ``append``,
            ``replace``, or ``merge``. See
            https://dlthub.com/docs/general-usage/incremental-loading#choosing-a-write-disposition.
        schema_contract (Optional[MetadataValue]): The dlt schema contract governing how schema
            changes are handled, either a shorthand string or a per-entity mapping. See
            https://dlthub.com/docs/general-usage/schema-contracts.
        resource (Optional[str]): The name of the dlt resource that produced the table.
        table_format (Optional[str]): The open table format used by the destination, e.g.
            ``iceberg`` or ``delta``, when configured.
    """

    write_disposition: MetadataValue | None = None
    schema_contract: MetadataValue | None = None
    resource: str | None = None
    table_format: str | None = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-dlt"

    @classmethod
    def from_resource(cls, resource: DltResource) -> "DagsterDltMetadataSet":
        """Build the metadata set from a dlt resource's hints, omitting values that are not set.

        These hints are known statically at definition time, so the metadata is attached to the
        asset spec rather than recomputed on every materialization.
        """
        table_format = resource.table_format
        return cls(
            write_disposition=_config_to_metadata_value(resource.write_disposition),
            schema_contract=_config_to_metadata_value(resource.schema_contract),
            resource=resource.name,
            table_format=table_format if isinstance(table_format, str) else None,
        )
