from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import InitVar, dataclass
from functools import cached_property
from pathlib import Path
from typing import AbstractSet, Any, NamedTuple, Optional, TypedDict, Union, cast  # noqa: UP035

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
from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._utils.warnings import disable_dagster_warnings
from sqlglot import MappingSchema, exp, parse_one, to_table
from sqlglot.expressions import normalize_table_name
from sqlglot.lineage import lineage
from sqlglot.optimizer import optimize

from dagster_dbt.asset_utils import (
    default_metadata_from_dbt_resource_props,
    get_asset_check_key_for_test,
    get_checks_on_sources_upstream_of_selected_assets,
)
from dagster_dbt.compat import REFABLE_NODE_TYPES, NodeStatus, NodeType, TestStatus
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest
from dagster_dbt.dbt_project import DbtProject

logger = get_dagster_logger()

# depending on the specific dbt version, any of these values
# may be used to indicate an empty value in a log message
_EMPTY_VALUES = {"", "None", None}


class EventHistoryMetadata(NamedTuple):
    columns: dict[str, dict[str, Any]]
    parents: dict[str, dict[str, Any]]


class CheckProperties(TypedDict):
    # Convenenience to abstract over AssetCheckResult and AssetCheckEvaluation
    passed: bool
    asset_key: AssetKey
    check_name: str
    severity: AssetCheckSeverity
    metadata: Mapping[str, Any]


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
        "exp.Query",
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
class DbtCliEventMessage(ABC):
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
    def has_column_lineage_metadata(self) -> bool:
        """Whether the event has column level lineage metadata."""
        return bool(self._event_history_metadata) and "parents" in self._event_history_metadata

    @cached_property
    def _unique_id(self) -> str:
        return self.raw_event["data"]["node_info"]["unique_id"]

    @cached_property
    def _raw_data(self) -> Mapping[str, Any]:
        return self.raw_event["data"]

    @cached_property
    def _raw_node_info(self) -> Mapping[str, Any]:
        return self.raw_event["data"]["node_info"]

    @property
    @abstractmethod
    def is_result_event(self) -> bool: ...

    def _is_model_execution_event(self, manifest: Mapping[str, Any]) -> bool:
        resource_props = self._get_resource_props(self._unique_id, manifest)
        materialized_type = (
            # check event info
            self._raw_node_info.get("materialized")
            # then top-level props
            or resource_props.get("materialized")
            # then config
            or resource_props.get("config", {}).get("materialized")
        )
        return (
            resource_props["resource_type"] in REFABLE_NODE_TYPES
            and materialized_type != "ephemeral"
            and self._get_node_status() == NodeStatus.Success
        )

    def _is_test_execution_event(self, manifest: Mapping[str, Any]) -> bool:
        resource_props = self._get_resource_props(self._unique_id, manifest)
        return resource_props["resource_type"] == NodeType.Test

    def _get_resource_props(self, unique_id: str, manifest: Mapping[str, Any]) -> dict[str, Any]:
        return manifest["nodes"][unique_id]

    def _get_execution_duration_metadata(self) -> Mapping[str, float]:
        raw_started_at = self._raw_node_info.get("node_started_at")
        raw_finished_at = self._raw_node_info.get("node_finished_at")

        has_started_at = raw_started_at not in _EMPTY_VALUES
        has_finished_at = raw_finished_at not in _EMPTY_VALUES

        if has_started_at and has_finished_at:
            started_at = dateutil.parser.isoparse(cast("str", raw_started_at))
            finished_at = dateutil.parser.isoparse(cast("str", raw_finished_at))
            duration = (finished_at - started_at).total_seconds()
            return {"Execution Duration": (finished_at - started_at).total_seconds()}
        else:
            # if model materialization is incremental microbatch, node_started_at and
            # node_finished_at are empty strings and require fallback to data.execution_time
            duration = self._raw_data.get("execution_time")

        return {"Execution Duration": duration} if duration else {}

    ###############
    # MODEL PARSING
    ###############

    def _get_column_schema_metadata(self, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            return default_metadata_from_dbt_resource_props(self._event_history_metadata)
        except Exception as e:
            logger.warning(
                "An error occurred while building column schema metadata from event history"
                f" `{self._event_history_metadata}` for the dbt resource"
                f" `{self._get_resource_props(self._unique_id, manifest)['original_file_path']}`."
                " Column schema metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )
            return {}

    def _get_default_metadata(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        return {
            **self._get_column_schema_metadata(manifest),
            **self._get_execution_duration_metadata(),
            "unique_id": self._unique_id,
            "invocation_id": self.raw_event["info"]["invocation_id"],
        }

    def _get_node_status(self) -> str:
        # if model materialization is incremental microbatch, node_status
        # property is "None", hence fall back to status
        raw_node_status = self._raw_node_info.get("node_status")
        return (
            raw_node_status
            if raw_node_status and raw_node_status not in _EMPTY_VALUES
            else self._raw_data["status"].lower()
        )

    def _get_lineage_metadata(
        self,
        translator: DagsterDbtTranslator,
        manifest: Mapping[str, Any],
        target_path: Optional[Path],
    ) -> Mapping[str, Any]:
        try:
            column_data = self._event_history_metadata.get("columns", {})
            parent_column_data = {
                parent_key: parent_data["columns"]
                for parent_key, parent_data in self._event_history_metadata.get(
                    "parents", {}
                ).items()
            }

            # Column lineage can only be built if initial metadata is provided.
            if self.has_column_lineage_metadata:
                return _build_column_lineage_metadata(
                    event_history_metadata=EventHistoryMetadata(
                        columns=column_data, parents=parent_column_data
                    ),
                    dbt_resource_props=self._get_resource_props(self._unique_id, manifest),
                    manifest=manifest,
                    dagster_dbt_translator=translator,
                    target_path=target_path,
                )
        except Exception as e:
            logger.warning(
                "An error occurred while building column lineage metadata for the dbt resource"
                f" `{self._get_resource_props(self._unique_id, manifest)['original_file_path']}`."
                " Lineage metadata will not be included in the event.\n\n"
                f"Exception: {e}",
                exc_info=True,
            )
        return {}

    def _get_materialization_metadata(
        self,
        translator: DagsterDbtTranslator,
        manifest: Mapping[str, Any],
        target_path: Optional[Path],
    ) -> dict[str, Any]:
        return {
            **self._get_default_metadata(manifest),
            **self._get_lineage_metadata(translator, manifest, target_path),
        }

    def _to_model_events(
        self,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]],
        target_path: Optional[Path],
        project: Optional[DbtProject],
    ) -> Iterator[Union[Output, AssetMaterialization]]:
        asset_key = dagster_dbt_translator.get_asset_spec(manifest, self._unique_id, project).key
        metadata = self._get_materialization_metadata(dagster_dbt_translator, manifest, target_path)
        if context and context.has_assets_def:
            yield Output(
                value=None, output_name=asset_key.to_python_identifier(), metadata=metadata
            )
        else:
            yield AssetMaterialization(asset_key=asset_key, metadata=metadata)

    ##############
    # TEST PARSING
    ##############

    def _get_check_execution_metadata(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        failure_count = self._raw_data.get("num_failures")
        return {
            **self._get_default_metadata(manifest),
            "status": self._get_node_status(),
            **({} if failure_count is None else {"dagster_dbt/failed_row_count": failure_count}),
        }

    @abstractmethod
    def _get_check_passed(self) -> bool: ...

    @abstractmethod
    def _get_check_severity(self) -> AssetCheckSeverity: ...

    def _get_check_properties(
        self, key: AssetCheckKey, manifest: Mapping[str, Any]
    ) -> CheckProperties:
        return CheckProperties(
            passed=self._get_check_passed(),
            asset_key=key.asset_key,
            check_name=key.name,
            severity=self._get_check_severity(),
            metadata=self._get_check_execution_metadata(manifest),
        )

    def _get_result_check_keys(
        self, context: Optional[Union[OpExecutionContext, AssetExecutionContext]]
    ) -> AbstractSet[AssetCheckKey]:
        """Returns the set of check keys for which we should emit AssetCheckResult events."""
        if context is None or not context.has_assets_def:
            return set()
        return {
            *context.selected_asset_check_keys,
            *get_checks_on_sources_upstream_of_selected_assets(
                assets_def=context.assets_def,
                selected_asset_keys=context.selected_asset_keys,
            ),
        }

    def _to_observation_events_for_test(
        self,
        key: Optional[AssetCheckKey],
        dagster_dbt_translator: DagsterDbtTranslator,
        validated_manifest: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> Iterator[AssetObservation]:
        resource_props = self._get_resource_props(self._unique_id, validated_manifest)
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
            test_name = resource_props["name"]
            additional_message = (
                (
                    f"`{test_name}` is a singular test with multiple dependencies."
                    " Configure an asset key in the test's dbt meta to load it as an"
                    " asset check.\n\n"
                )
                if not key
                else ""
            )

            message = (
                "Logging an `AssetObservation` instead of an `AssetCheckResult`"
                f" for dbt test `{test_name}`.\n\n"
                f"{additional_message}"
                "This test was not included in Dagster's asset check"
                " selection, and was likely executed due to dbt indirect selection."
            )
            logger.warning(message)

        for upstream_unique_id in resource_props["depends_on"]["nodes"]:
            upstream_resource_props: dict[str, Any] = validated_manifest["nodes"].get(
                upstream_unique_id
            ) or validated_manifest["sources"].get(upstream_unique_id)
            upstream_asset_key = dagster_dbt_translator.get_asset_key(upstream_resource_props)

            yield AssetObservation(
                asset_key=upstream_asset_key, metadata=metadata, description=message
            )

    def _to_test_events(
        self,
        manifest: Mapping[str, Any],
        translator: DagsterDbtTranslator,
        project: Optional[DbtProject],
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]],
    ) -> Iterator[Union[AssetCheckResult, AssetCheckEvaluation, AssetObservation]]:
        """Converts a dbt CLI event to a set of Dagster events corresponding to a test execution."""
        key = get_asset_check_key_for_test(manifest, translator, self._unique_id, project=project)

        has_assets_def = context is not None and context.has_assets_def

        if key is not None and has_assets_def and key in self._get_result_check_keys(context):
            # key was expected to be evaluated, use AssetCheckResult
            properties = self._get_check_properties(key, manifest)
            yield AssetCheckResult(**properties)
            return
        elif key is not None and not has_assets_def:
            # in an op definition, we don't have an assets def, so we use AssetCheckEvaluation
            properties = self._get_check_properties(key, manifest)
            yield AssetCheckEvaluation(**properties)
            return

        # fallback case, emit observation events if we have no key to associate with the
        # test, or if the test was not expected to be evaluated.
        metadata = self._get_check_execution_metadata(manifest)
        yield from self._to_observation_events_for_test(
            key=key,
            dagster_dbt_translator=translator,
            validated_manifest=manifest,
            metadata=metadata,
        )

    @public
    def to_default_asset_events(
        self,
        manifest: DbtManifestParam,
        dagster_dbt_translator: DagsterDbtTranslator = DagsterDbtTranslator(),
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = None,
        target_path: Optional[Path] = None,
        project: Optional[DbtProject] = None,
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
        if not self.is_result_event:
            return

        dagster_dbt_translator = validate_translator(dagster_dbt_translator)
        manifest = validate_manifest(manifest)

        if self._is_model_execution_event(manifest):
            yield from self._to_model_events(
                manifest, dagster_dbt_translator, context, target_path, project
            )
        if self._is_test_execution_event(manifest):
            yield from self._to_test_events(manifest, dagster_dbt_translator, project, context)


class DbtCoreCliEventMessage(DbtCliEventMessage):
    """Represents a dbt CLI event that was produced using the dbt Core engine."""

    @property
    def is_result_event(self) -> bool:
        return self.raw_event["info"]["name"] in set(
            ["LogSeedResult", "LogModelResult", "LogSnapshotResult", "LogTestResult"]
        ) and not self.raw_event["data"].get("node_info", {}).get("unique_id", "").startswith(
            "unit_test"
        )

    def _get_check_passed(self) -> bool:
        return self._get_node_status() == TestStatus.Pass

    def _get_check_severity(self) -> AssetCheckSeverity:
        node_status = self._get_node_status()
        return (
            AssetCheckSeverity.WARN if node_status == NodeStatus.Warn else AssetCheckSeverity.ERROR
        )


class DbtFusionCliEventMessage(DbtCliEventMessage):
    """Represents a dbt CLI event that was produced using the dbt Fusion engine."""

    @property
    def is_result_event(self) -> bool:
        return self.raw_event["info"]["name"] == "NodeFinished"

    def _get_check_passed(self) -> bool:
        return self._get_node_status() == NodeStatus.Success

    def _get_check_severity(self) -> AssetCheckSeverity:
        node_status = self._get_node_status()
        return (
            AssetCheckSeverity.WARN if node_status == NodeStatus.Warn else AssetCheckSeverity.ERROR
        )
