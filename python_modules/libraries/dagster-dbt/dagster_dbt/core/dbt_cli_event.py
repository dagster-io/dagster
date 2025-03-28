from collections.abc import Iterator, Mapping, Sequence
from dataclasses import InitVar, dataclass
from pathlib import Path
from typing import AbstractSet, Any, NamedTuple, Optional, Union, cast  # noqa: UP035

import dateutil.parser
from dagster import (
    AssetCheckResult,
    AssetCheckSeverity,
    AssetExecutionContext,
    AssetMaterialization,
    AssetObservation,
    OpExecutionContext,
    Output,
    TableColumnDep,
    TableColumnLineage,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._utils.warnings import disable_dagster_warnings
from dbt.contracts.results import NodeStatus, TestStatus
from dbt.node_types import NodeType
from dbt.version import __version__ as dbt_version
from packaging import version
from sqlglot import MappingSchema, exp, parse_one, to_table
from sqlglot.expressions import normalize_table_name
from sqlglot.lineage import lineage
from sqlglot.optimizer import optimize

from dagster_dbt.asset_utils import (
    default_metadata_from_dbt_resource_props,
    get_asset_check_key_for_test,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest

IS_DBT_CORE_VERSION_LESS_THAN_1_8_0 = version.parse(dbt_version) < version.parse("1.8.0")
if IS_DBT_CORE_VERSION_LESS_THAN_1_8_0:
    REFABLE_NODE_TYPES = NodeType.refable()  # type: ignore
else:
    from dbt.node_types import REFABLE_NODE_TYPES as REFABLE_NODE_TYPES

logger = get_dagster_logger()


class EventHistoryMetadata(NamedTuple):
    columns: dict[str, dict[str, Any]]
    parents: dict[str, dict[str, Any]]


def _build_column_lineage_metadata(
    event_history_metadata: EventHistoryMetadata,
    dbt_resource_props: dict[str, Any],
    manifest: Mapping[str, Any],
    dagster_dbt_translator: DagsterDbtTranslator,
    target_path: Optional[Path],
) -> dict[str, Any]:
    """Process the lineage metadata for a dbt CLI event.

    Args:
        event_history_metadata (EventHistoryMetadata): Unprocessed column type data and map of
            parent relation names to their column type data.
        dbt_resource_props (Dict[str, Any]): The dbt resource properties for the given event.
        manifest (Mapping[str, Any]): The dbt manifest blob.
        dagster_dbt_translator (DagsterDbtTranslator): The translator for dbt nodes to Dagster assets.
        target_path (Path): The path to the dbt target folder.

    Returns:
        Dict[str, Any]: The lineage metadata.
    """
    if (
        # Column lineage can only be built if initial metadata is provided.
        not target_path
    ):
        return {}

    event_node_info: dict[str, Any] = dbt_resource_props
    unique_id: str = event_node_info["unique_id"]

    node_resource_type: str = event_node_info["resource_type"]

    if node_resource_type not in REFABLE_NODE_TYPES:
        return {}

    # If the unique_id is a seed, then we don't need to process lineage.
    if unique_id.startswith("seed"):
        return {}

    # 1. Retrieve the current node's SQL file and its parents' column schemas.
    sql_dialect = manifest["metadata"]["adapter_type"]
    sqlglot_mapping_schema = MappingSchema(dialect=sql_dialect)

    parent_relation_metadata_by_relation_name = {
        **event_history_metadata.parents,
        # Include the current node's column schema to optimize self-referential models.
        dbt_resource_props["relation_name"]: event_history_metadata.columns,
    }
    for (
        parent_relation_name,
        parent_relation_metadata,
    ) in parent_relation_metadata_by_relation_name.items():
        sqlglot_mapping_schema.add_table(
            table=to_table(parent_relation_name, dialect=sql_dialect),
            column_mapping={
                column_name: column_meta["data_type"]
                for column_name, column_meta in parent_relation_metadata.items()
            },
            dialect=sql_dialect,
        )

    package_name = dbt_resource_props["package_name"]
    node_sql_path = target_path.joinpath(
        "compiled",
        package_name,
        dbt_resource_props["original_file_path"].replace("\\", "/"),
    )
    optimized_node_ast = cast(
        exp.Query,
        optimize(
            parse_one(sql=node_sql_path.read_text(), dialect=sql_dialect),
            schema=sqlglot_mapping_schema,
            dialect=sql_dialect,
        ),
    )

    # 2. Retrieve the column names from the current node.
    schema_column_names = {column.lower() for column in event_history_metadata.columns.keys()}
    sqlglot_column_names = set(optimized_node_ast.named_selects)

    # 3. For each column, retrieve its dependencies on upstream columns from direct parents.
    dbt_parent_resource_props_by_relation_name: dict[str, dict[str, Any]] = {}
    for parent_unique_id in dbt_resource_props["depends_on"]["nodes"]:
        is_resource_type_source = parent_unique_id.startswith("source")
        parent_dbt_resource_props = (
            manifest["sources"] if is_resource_type_source else manifest["nodes"]
        )[parent_unique_id]
        parent_relation_name = normalize_table_name(
            to_table(parent_dbt_resource_props["relation_name"], dialect=sql_dialect),
            dialect=sql_dialect,
        )

        dbt_parent_resource_props_by_relation_name[parent_relation_name] = parent_dbt_resource_props

    normalized_sqlglot_column_names = {
        sqlglot_column.lower() for sqlglot_column in sqlglot_column_names
    }
    implicit_alias_column_names = {
        column for column in schema_column_names if column not in normalized_sqlglot_column_names
    }

    deps_by_column: dict[str, Sequence[TableColumnDep]] = {}
    if implicit_alias_column_names:
        logger.warning(
            "The following columns are implicitly aliased and will be marked with an "
            f" empty list column dependencies: `{implicit_alias_column_names}`."
        )

        deps_by_column = {column: [] for column in implicit_alias_column_names}

    for column_name in sqlglot_column_names:
        if column_name.lower() not in schema_column_names:
            continue

        column_deps: set[TableColumnDep] = set()
        for sqlglot_lineage_node in lineage(
            column=column_name,
            sql=optimized_node_ast,
            schema=sqlglot_mapping_schema,
            dialect=sql_dialect,
        ).walk():
            # Only the leaves of the lineage graph contain relevant information.
            if sqlglot_lineage_node.downstream:
                continue

            # Attempt to find a table in the lineage node.
            table = sqlglot_lineage_node.expression.find(exp.Table)
            if not table:
                continue

            # Attempt to retrieve the table's associated asset key and column.
            parent_column_name = exp.to_column(sqlglot_lineage_node.name).name.lower()
            parent_relation_name = normalize_table_name(table, dialect=sql_dialect)
            parent_resource_props = dbt_parent_resource_props_by_relation_name.get(
                parent_relation_name
            )
            if not parent_resource_props:
                continue

            # Add the column dependency.
            column_deps.add(
                TableColumnDep(
                    asset_key=dagster_dbt_translator.get_asset_key(parent_resource_props),
                    column_name=parent_column_name,
                )
            )

        deps_by_column[column_name.lower()] = list(column_deps)

    # 4. Render the lineage as metadata.
    with disable_dagster_warnings():
        return dict(
            TableMetadataSet(column_lineage=TableColumnLineage(deps_by_column=deps_by_column))
        )


@dataclass
class DbtCliEventMessage:
    """The representation of a dbt CLI event.

    Args:
        raw_event (Dict[str, Any]): The raw event dictionary.
            See https://docs.getdbt.com/reference/events-logging#structured-logging for more
            information.
        event_history_metadata (Dict[str, Any]): A dictionary of metadata about the
            current event, gathered from previous historical events.
    """

    raw_event: dict[str, Any]
    event_history_metadata: InitVar[dict[str, Any]]

    def __post_init__(self, event_history_metadata: dict[str, Any]):
        self._event_history_metadata = event_history_metadata

    def __str__(self) -> str:
        return self.raw_event["info"]["msg"]

    @property
    def log_level(self) -> str:
        """The log level of the event."""
        return self.raw_event["info"]["level"]

    @property
    def has_column_lineage_metadata(self) -> bool:
        """Whether the event has column level lineage metadata."""
        return bool(self._event_history_metadata) and "parents" in self._event_history_metadata

    @staticmethod
    def is_result_event(raw_event: dict[str, Any]) -> bool:
        return raw_event["info"]["name"] in set(
            ["LogSeedResult", "LogModelResult", "LogSnapshotResult", "LogTestResult"]
        ) and not raw_event["data"]["node_info"]["unique_id"].startswith("unit_test")

    def _yield_observation_events_for_test(
        self,
        dagster_dbt_translator: DagsterDbtTranslator,
        validated_manifest: Mapping[str, Any],
        upstream_unique_ids: AbstractSet[str],
        metadata: Mapping[str, Any],
        description: Optional[str] = None,
    ) -> Iterator[AssetObservation]:
        for upstream_unique_id in upstream_unique_ids:
            upstream_resource_props: dict[str, Any] = validated_manifest["nodes"].get(
                upstream_unique_id
            ) or validated_manifest["sources"].get(upstream_unique_id)
            upstream_asset_key = dagster_dbt_translator.get_asset_key(upstream_resource_props)

            yield AssetObservation(
                asset_key=upstream_asset_key,
                metadata=metadata,
                description=description,
            )

    @public
    def to_default_asset_events(
        self,
        manifest: DbtManifestParam,
        dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = None,
        target_path: Optional[Path] = None,
    ) -> Iterator[
        Union[
            Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation
        ]
    ]:
        """Convert a dbt CLI event to a set of corresponding Dagster events.

        Args:
            manifest (Union[Mapping[str, Any], str, Path]): The dbt manifest blob.
            dagster_dbt_translator (DagsterDbtTranslator): Optionally, a custom translator for
                linking dbt nodes to Dagster assets.
            context (Optional[Union[OpExecutionContext, AssetExecutionContext]]): The execution context.
            target_path (Optional[Path]): An explicit path to a target folder used to retrieve
                dbt artifacts while generating events.

        Returns:
            Iterator[Union[Output, AssetMaterialization, AssetObservation, AssetCheckResult, AssetCheckEvaluation]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models, seeds, snapshots.)
                - AssetCheckResult for dbt test results that are enabled as asset checks.
                - AssetObservation for dbt test results that are not enabled as asset checks.

               In a Dagster op definition, the following are yielded:
                - AssetMaterialization refables (e.g. models, seeds, snapshots.)
                - AssetCheckEvaluation for dbt test results that are enabled as asset checks.
                - AssetObservation for dbt test results that are not enabled as asset checks.
        """
        if not self.is_result_event(self.raw_event):
            return

        event_node_info: dict[str, Any] = self.raw_event["data"].get("node_info")
        if not event_node_info:
            return

        dagster_dbt_translator = validate_translator(dagster_dbt_translator)
        manifest = validate_manifest(manifest)

        if not manifest:
            logger.info(
                "No dbt manifest was provided. Dagster events for dbt tests will not be created."
            )

        unique_id: str = event_node_info["unique_id"]
        invocation_id: str = self.raw_event["info"]["invocation_id"]
        dbt_resource_props = manifest["nodes"][unique_id]

        column_schema_metadata = {}
        try:
            column_schema_metadata = default_metadata_from_dbt_resource_props(
                self._event_history_metadata
            )
        except Exception as e:
            logger.warning(
                "An error occurred while building column schema metadata from event history"
                f" `{self._event_history_metadata}` for the dbt resource"
                f" `{dbt_resource_props['original_file_path']}`."
                " Column schema metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )

        default_metadata = {
            **column_schema_metadata,
            "unique_id": unique_id,
            "invocation_id": invocation_id,
        }

        if event_node_info.get("node_started_at") in ["", "None", None] and event_node_info.get(
            "node_finished_at"
        ) in ["", "None", None]:
            # if model materialization is incremental microbatch, node_started_at and node_finished_at are empty strings
            # and require fallback to data.execution_time
            default_metadata["Execution Duration"] = self.raw_event["data"]["execution_time"]
        elif event_node_info.get("node_started_at") and event_node_info.get("node_finished_at"):
            started_at = dateutil.parser.isoparse(event_node_info["node_started_at"])
            finished_at = dateutil.parser.isoparse(event_node_info["node_finished_at"])
            default_metadata["Execution Duration"] = (finished_at - started_at).total_seconds()

        has_asset_def: bool = bool(context and context.has_assets_def)

        node_resource_type: str = event_node_info["resource_type"]
        # if model materialization is incremental microbatch, node_status property is "None", hence fall back to status
        node_status: str = (
            self.raw_event["data"]["status"].lower()
            if event_node_info["node_status"] in ["", "None", None]
            else event_node_info["node_status"]
        )
        node_materialization: str = self.raw_event["data"]["node_info"]["materialized"]

        is_node_ephemeral = node_materialization == "ephemeral"
        is_node_successful = node_status == NodeStatus.Success
        is_node_finished = bool(event_node_info.get("node_finished_at"))
        if (
            node_resource_type in REFABLE_NODE_TYPES
            and is_node_successful
            and not is_node_ephemeral
        ):
            lineage_metadata = {}
            try:
                column_data = self._event_history_metadata.get("columns", {})
                parent_column_data = {
                    parent_key: parent_data["columns"]
                    for parent_key, parent_data in self._event_history_metadata.get(
                        "parents", {}
                    ).items()
                }

                if (
                    # Column lineage can only be built if initial metadata is provided.
                    self.has_column_lineage_metadata
                ):
                    lineage_metadata = _build_column_lineage_metadata(
                        event_history_metadata=EventHistoryMetadata(
                            columns=column_data, parents=parent_column_data
                        ),
                        dbt_resource_props=dbt_resource_props,
                        manifest=manifest,
                        dagster_dbt_translator=dagster_dbt_translator,
                        target_path=target_path,
                    )
            except Exception as e:
                logger.warning(
                    "An error occurred while building column lineage metadata for the dbt resource"
                    f" `{dbt_resource_props['original_file_path']}`."
                    " Lineage metadata will not be included in the event.\n\n"
                    f"Exception: {e}",
                    exc_info=True,
                )

            dbt_resource_props = manifest["nodes"][unique_id]
            asset_key = dagster_dbt_translator.get_asset_key(dbt_resource_props)
            if context and has_asset_def:
                yield Output(
                    value=None,
                    output_name=asset_key.to_python_identifier(),
                    metadata={
                        **default_metadata,
                        **lineage_metadata,
                    },
                )
            else:
                yield AssetMaterialization(
                    asset_key=asset_key,
                    metadata={
                        **default_metadata,
                        **lineage_metadata,
                    },
                )
        elif manifest and node_resource_type == NodeType.Test and is_node_finished:
            test_resource_props = manifest["nodes"][unique_id]
            upstream_unique_ids: AbstractSet[str] = set(test_resource_props["depends_on"]["nodes"])
            metadata = {
                **default_metadata,
                "status": node_status,
            }
            if self.raw_event["data"].get("num_failures") is not None:
                metadata["dagster_dbt/failed_row_count"] = self.raw_event["data"]["num_failures"]

            asset_check_key = get_asset_check_key_for_test(
                manifest, dagster_dbt_translator, test_unique_id=unique_id
            )

            if (
                context
                and has_asset_def
                and asset_check_key is not None
                and asset_check_key in context.selected_asset_check_keys
            ):
                # The test is an asset check in an asset, so yield an `AssetCheckResult`.
                yield AssetCheckResult(
                    passed=node_status == TestStatus.Pass,
                    asset_key=asset_check_key.asset_key,
                    check_name=asset_check_key.name,
                    metadata=metadata,
                    severity=(
                        AssetCheckSeverity.WARN
                        if node_status == TestStatus.Warn
                        else AssetCheckSeverity.ERROR
                    ),
                )
            elif not has_asset_def and asset_check_key is not None:
                # The test is an asset check in an op, so yield an `AssetCheckEvaluation`.
                yield AssetCheckEvaluation(
                    passed=node_status == TestStatus.Pass,
                    asset_key=asset_check_key.asset_key,
                    check_name=asset_check_key.name,
                    metadata=metadata,
                    severity=(
                        AssetCheckSeverity.WARN
                        if node_status == TestStatus.Warn
                        else AssetCheckSeverity.ERROR
                    ),
                )
            else:
                # since there is no asset check key, we log observations instead
                message = None

                # dbt's default indirect selection (eager) will select relationship tests
                # on unselected assets, if they're compared with a selected asset.
                # This doesn't match Dagster's default check selection which is to only
                # select checks on selected assets. When we use eager, we may receive
                # unexpected test results so we log those as observations as if
                # asset checks were disabled.
                if dagster_dbt_translator.settings.enable_asset_checks:
                    # If the test did not have an asset key associated with it, it was a singular
                    # test with multiple dependencies without a configured asset key.
                    test_name = test_resource_props["name"]
                    additional_message = (
                        (
                            f"`{test_name}` is a singular test with multiple dependencies."
                            " Configure an asset key in the test's dbt meta to load it as an"
                            " asset check.\n\n"
                        )
                        if not asset_check_key
                        else ""
                    )

                    message = (
                        "Logging an `AssetObservation` instead of an `AssetCheckResult`"
                        f" for dbt test `{test_name}`.\n\n"
                        f"{additional_message}"
                        "This test was included in Dagster's asset check"
                        " selection, and was likely executed due to dbt indirect selection."
                    )
                    logger.warning(message)

                yield from self._yield_observation_events_for_test(
                    dagster_dbt_translator=dagster_dbt_translator,
                    validated_manifest=manifest,
                    upstream_unique_ids=upstream_unique_ids,
                    metadata=metadata,
                    description=message,
                )
