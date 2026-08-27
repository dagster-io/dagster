from collections.abc import Mapping
from typing import Any

from dagster import MetadataValue
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dlt import Pipeline
from dlt.sources import DltResource


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

    Some entries are known statically at definition time (from the dlt resource's hints and the
    pipeline's destination) and are attached to the asset spec; others vary per run and are attached
    to each materialization. All fields are optional.

    Args:
        write_disposition (Optional[MetadataValue]): How dlt writes the table, e.g. ``append``,
            ``replace``, or ``merge``. See
            https://dlthub.com/docs/general-usage/incremental-loading#choosing-a-write-disposition.
        schema_contract (Optional[MetadataValue]): The dlt schema contract governing how schema
            changes are handled, either a shorthand string or a per-entity mapping. See
            https://dlthub.com/docs/general-usage/schema-contracts.
        resource (Optional[str]): The name of the dlt resource that produced the table.
        table_name (Optional[str]): The name of the destination table the resource loads into.
            Defaults to the resource name when no explicit ``table_name`` hint is set.
        table_format (Optional[str]): The open table format used by the destination, e.g.
            ``iceberg`` or ``delta``, when configured.
        destination_name (Optional[str]): The name of the dlt destination, e.g. ``duckdb``.
        destination_type (Optional[str]): The fully-qualified dlt destination type, e.g.
            ``dlt.destinations.duckdb``.
        dataset_name (Optional[str]): The name of the dlt dataset (destination schema/namespace)
            the pipeline loads into.
        first_run (Optional[bool]): Whether this was the first run of the pipeline.
        started_at (Optional[str]): When the load started.
        finished_at (Optional[str]): When the load finished.
        rows_loaded (Optional[int]): The number of rows dlt loaded into the table on a given run.
            This is distinct from ``dagster/row_count``, which is the destination table's total
            row count.
        jobs (Optional[MetadataValue]): The dlt load jobs that targeted this table on a given run.
    """

    # Definition-time (static) fields.
    write_disposition: MetadataValue | None = None
    schema_contract: MetadataValue | None = None
    resource: str | None = None
    table_name: str | None = None
    table_format: str | None = None
    destination_name: str | None = None
    destination_type: str | None = None
    dataset_name: str | None = None
    # Per-run fields, attached to materializations.
    first_run: bool | None = None
    started_at: str | None = None
    finished_at: str | None = None
    rows_loaded: int | None = None
    jobs: MetadataValue | None = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-dlt"

    @classmethod
    def from_resource(cls, resource: DltResource) -> "DagsterDltMetadataSet":
        """Build the metadata set from a dlt resource's hints, omitting values that are not set.

        These hints are known statically at definition time, so the metadata is attached to the
        asset spec.
        """
        table_format = resource.table_format
        # ``table_name`` may be a callable for dynamically-computed hints, in which case dlt falls
        # back to the resource name for the destination table.
        table_name = resource.table_name
        if not isinstance(table_name, str):
            table_name = resource.name
        return cls(
            write_disposition=_config_to_metadata_value(resource.write_disposition),
            schema_contract=_config_to_metadata_value(resource.schema_contract),
            resource=resource.name,
            table_name=table_name,
            table_format=table_format if isinstance(table_format, str) else None,
        )

    @classmethod
    def from_pipeline(cls, pipeline: Pipeline) -> "DagsterDltMetadataSet":
        """Build the destination-related metadata from a dlt pipeline.

        These are fixed when the pipeline is defined, so the metadata is attached to the asset spec.
        """
        destination = pipeline.destination
        return cls(
            destination_name=destination.destination_name if destination else None,
            destination_type=destination.destination_type if destination else None,
            dataset_name=pipeline.dataset_name,
        )
