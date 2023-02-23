from __future__ import annotations

from enum import Enum
from hashlib import sha256
from typing import TYPE_CHECKING, Callable, Iterator, Mapping, NamedTuple, Optional, Sequence, Union

from typing_extensions import Final

from dagster import _check as check
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.definitions.asset_graph import AssetGraph
    from dagster._core.definitions.events import (
        AssetKey,
        AssetMaterialization,
        AssetObservation,
        Materialization,
    )
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance import DagsterInstance


class UnknownValue:
    pass


def foo(x):
    return False


UNKNOWN_VALUE: Final[UnknownValue] = UnknownValue()


class LogicalVersion(
    NamedTuple(
        "_LogicalVersion",
        [("value", str)],
    )
):
    """(Experimental) Represents a logical version for an asset.

    Args:
        value (str): An arbitrary string representing a logical version.
    """

    def __new__(
        cls,
        value: str,
    ):
        return super(LogicalVersion, cls).__new__(
            cls,
            value=check.str_param(value, "value"),
        )


DEFAULT_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("INITIAL")
NULL_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("NULL")
UNKNOWN_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("UNKNOWN")


class LogicalVersionProvenance(
    NamedTuple(
        "_LogicalVersionProvenance",
        [
            ("code_version", str),
            ("input_logical_versions", Mapping["AssetKey", LogicalVersion]),
        ],
    )
):
    def __new__(
        cls,
        code_version: str,
        input_logical_versions: Mapping["AssetKey", LogicalVersion],
    ):
        from dagster._core.definitions.events import AssetKey

        return super(LogicalVersionProvenance, cls).__new__(
            cls,
            code_version=check.str_param(code_version, "code_version"),
            input_logical_versions=check.mapping_param(
                input_logical_versions,
                "input_logical_versions",
                key_type=AssetKey,
                value_type=LogicalVersion,
            ),
        )

    @staticmethod
    def from_tags(tags: Mapping[str, str]) -> Optional[LogicalVersionProvenance]:
        from dagster._core.definitions.events import AssetKey

        code_version = tags.get(CODE_VERSION_TAG_KEY)
        if code_version is None:
            return None
        start_index = len(INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX) + 1
        input_logical_versions = {
            AssetKey.from_user_string(k[start_index:]): LogicalVersion(tags[k])
            for k, v in tags.items()
            if k.startswith(INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX)
        }
        return LogicalVersionProvenance(code_version, input_logical_versions)


# ########################
# ##### TAG KEYS
# ########################

LOGICAL_VERSION_TAG_KEY: Final[str] = "dagster/logical_version"
CODE_VERSION_TAG_KEY: Final[str] = "dagster/code_version"
INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX: Final[str] = "dagster/input_logical_version"
INPUT_EVENT_POINTER_TAG_KEY_PREFIX: Final[str] = "dagster/input_event_pointer"


def get_input_logical_version_tag_key(input_key: "AssetKey") -> str:
    return f"{INPUT_LOGICAL_VERSION_TAG_KEY_PREFIX}/{input_key.to_user_string()}"


def get_input_event_pointer_tag_key(input_key: "AssetKey") -> str:
    return f"{INPUT_EVENT_POINTER_TAG_KEY_PREFIX}/{input_key.to_user_string()}"


# ########################
# ##### COMPUTE / EXTRACT
# ########################


def compute_logical_version(
    code_version: Union[str, UnknownValue],
    input_logical_versions: Mapping["AssetKey", LogicalVersion],
) -> LogicalVersion:
    """Compute a logical version from inputs.

    Args:
        code_version (LogicalVersion): The code version of the computation.
        input_logical_versions (Mapping[AssetKey, LogicalVersion]): The logical versions of the inputs.

    Returns:
        LogicalVersion: The computed logical version.
    """
    from dagster._core.definitions.events import AssetKey

    check.inst_param(code_version, "code_version", (str, UnknownValue))
    check.mapping_param(
        input_logical_versions, "input_versions", key_type=AssetKey, value_type=LogicalVersion
    )

    if (
        isinstance(code_version, UnknownValue)
        or UNKNOWN_LOGICAL_VERSION in input_logical_versions.values()
    ):
        return UNKNOWN_LOGICAL_VERSION

    ordered_input_versions = [
        input_logical_versions[k] for k in sorted(input_logical_versions.keys(), key=str)
    ]
    all_inputs = (code_version, *(v.value for v in ordered_input_versions))

    hash_sig = sha256()
    hash_sig.update(bytearray("".join(all_inputs), "utf8"))
    return LogicalVersion(hash_sig.hexdigest())


def extract_logical_version_from_entry(
    entry: EventLogEntry,
) -> Optional[LogicalVersion]:
    event_data = _extract_event_data_from_entry(entry)
    tags = event_data.tags or {}
    value = tags.get(LOGICAL_VERSION_TAG_KEY)
    return None if value is None else LogicalVersion(value)


def extract_logical_version_provenance_from_entry(
    entry: EventLogEntry,
) -> Optional[LogicalVersionProvenance]:
    event_data = _extract_event_data_from_entry(entry)
    tags = event_data.tags or {}
    return LogicalVersionProvenance.from_tags(tags)


def _extract_event_data_from_entry(
    entry: EventLogEntry,
) -> Union["AssetMaterialization", "AssetObservation"]:
    from dagster._core.definitions.events import AssetMaterialization, AssetObservation
    from dagster._core.events import AssetObservationData, StepMaterializationData

    data = check.not_none(entry.dagster_event).event_specific_data
    event_data: Union[Materialization, AssetMaterialization, AssetObservation]
    if isinstance(data, StepMaterializationData):
        event_data = data.materialization
    elif isinstance(data, AssetObservationData):
        event_data = data.asset_observation
    else:
        check.failed(f"Unexpected event type {type(data)}")

    assert isinstance(event_data, (AssetMaterialization, AssetObservation))
    return event_data


# ########################
# ##### STALENESS OPERATIONS
# ########################


class StaleStatus(Enum):
    STALE = "STALE"
    FRESH = "FRESH"
    UNKNOWN = "UNKNOWN"


class StaleStatusCause(NamedTuple):
    status: StaleStatus
    key: AssetKey
    reason: str


class CachingStaleStatusResolver:
    """
    Used to resolve logical version information. Avoids redundant database
    calls that would otherwise occur. Intended for use within the scope of a
    single "request" (e.g. GQL request, RunRequest resolution).
    """

    _instance: "DagsterInstance"
    _asset_graph: Optional["AssetGraph"]
    _asset_graph_load_fn: Optional[Callable[[], "AssetGraph"]]

    def __init__(
        self,
        instance: "DagsterInstance",
        asset_graph: Union["AssetGraph", Callable[[], "AssetGraph"]],
    ):
        from dagster._core.definitions.asset_graph import AssetGraph

        self._instance = instance
        if isinstance(asset_graph, AssetGraph):
            self._asset_graph = asset_graph
            self._asset_graph_load_fn = None
        else:
            self._asset_graph = None
            self._asset_graph_load_fn = asset_graph

    def get_status(self, key: AssetKey) -> StaleStatus:
        return self._get_status(key=key)

    def get_status_causes(self, key: AssetKey) -> Sequence[StaleStatusCause]:
        return self._get_status_causes(key=key)

    def get_current_logical_version(self, key: AssetKey) -> LogicalVersion:
        return self._get_current_logical_version(key=key)

    def get_projected_logical_version(self, key: AssetKey) -> LogicalVersion:
        return self._get_projected_logical_version(key=key)

    @cached_method
    def _get_status(self, key: AssetKey) -> StaleStatus:
        if self.asset_graph.get_partitions_def(key):
            return StaleStatus.UNKNOWN
        else:
            causes = self._get_status_causes(key=key)
            return StaleStatus.FRESH if len(causes) == 0 else causes[0].status

        current_version = self._get_current_logical_version(key=key)
        projected_version = self._get_projected_logical_version(key=key)
        if projected_version == UNKNOWN_LOGICAL_VERSION:
            return StaleStatus.UNKNOWN
        elif projected_version == current_version:  # always true for source assets
            return StaleStatus.FRESH
        else:
            return StaleStatus.STALE

    @cached_method
    def _get_status_causes(self, key: AssetKey) -> Sequence[StaleStatusCause]:
        current_version = self._get_current_logical_version(key=key)
        projected_version = self._get_projected_logical_version(key=key)
        if current_version == projected_version:
            return []
        elif current_version == NULL_LOGICAL_VERSION:
            return [StaleStatusCause(StaleStatus.STALE, key, "never materialized")]
        else:
            return list(self._get_stale_status_causes_materialized(key))

    def _get_stale_status_causes_materialized(self, key: AssetKey) -> Iterator[StaleStatusCause]:
        code_version = self.asset_graph.get_code_version(key)
        provenance = self._get_current_logical_version_provenance(key=key)
        proj_dep_keys = self.asset_graph.get_parents(key)

        if provenance:
            prov_versions = provenance.input_logical_versions
            all_dep_keys = sorted(set(proj_dep_keys).union(prov_versions.keys()))
            for dep_key in all_dep_keys:
                if dep_key not in prov_versions:
                    yield StaleStatusCause(
                        StaleStatus.STALE, key, f"new input: {dep_key.to_user_string()}"
                    )
                elif dep_key not in proj_dep_keys:
                    yield StaleStatusCause(
                        StaleStatus.STALE, key, f"removed input: {dep_key.to_user_string()}"
                    )
                elif prov_versions[dep_key] != self._get_current_logical_version(key=dep_key):
                    yield StaleStatusCause(
                        StaleStatus.STALE, key, f"updated input: {dep_key.to_user_string()}"
                    )
                elif prov_versions[dep_key] != self._get_projected_logical_version(key=dep_key):
                    yield StaleStatusCause(
                        StaleStatus.STALE, key, f"stale input: {dep_key.to_user_string()}"
                    )

            if code_version is not None and code_version != provenance.code_version:
                yield StaleStatusCause(StaleStatus.STALE, key, "updated code version")

        if code_version is None:
            yield StaleStatusCause(StaleStatus.UNKNOWN, key, "code version unknown")
        elif provenance is None or provenance.code_version is None:
            yield StaleStatusCause(StaleStatus.UNKNOWN, key, "previous code version unknown")

        for dep_key in proj_dep_keys:
            yield from self._get_status_causes(key=dep_key)

    @property
    def asset_graph(self) -> "AssetGraph":
        if self._asset_graph is None:
            self._asset_graph = check.not_none(self._asset_graph_load_fn)()
        return self._asset_graph

    @cached_method
    def _get_current_logical_version(self, *, key: AssetKey) -> LogicalVersion:
        is_source = self.asset_graph.is_source(key)
        event = self._instance.get_latest_logical_version_record(
            key,
            is_source,
        )
        if event is None and is_source:
            return DEFAULT_LOGICAL_VERSION
        elif event is None:
            return NULL_LOGICAL_VERSION
        else:
            logical_version = extract_logical_version_from_entry(event.event_log_entry)
            return logical_version or DEFAULT_LOGICAL_VERSION

    @cached_method
    def _get_projected_logical_version(self, *, key: AssetKey) -> LogicalVersion:
        if self.asset_graph.get_partitions_def(key):
            return UNKNOWN_LOGICAL_VERSION
        elif self.asset_graph.is_source(key):
            event = self._instance.get_latest_logical_version_record(key, True)
            if event:
                version = (
                    extract_logical_version_from_entry(event.event_log_entry)
                    or DEFAULT_LOGICAL_VERSION
                )
            else:
                version = DEFAULT_LOGICAL_VERSION
        elif self.asset_graph.get_code_version(key) is not None:
            version = self._compute_projected_new_materialization_logical_version(key)
        else:
            materialization = self._get_latest_materialization_event(key=key)
            if materialization is None:  # never been materialized
                version = self._compute_projected_new_materialization_logical_version(key)
            else:
                current_logical_version = self._get_current_logical_version(key=key)
                provenance = self._get_current_logical_version_provenance(key=key)
                if (
                    current_logical_version
                    is None  # old materialization event before logical versions
                    or provenance is None  # should never happen
                    or self._is_provenance_stale(key, provenance)
                ):
                    version = self._compute_projected_new_materialization_logical_version(key)
                else:
                    version = current_logical_version
        return version

    @cached_method
    def _get_latest_materialization_event(self, *, key: AssetKey) -> Optional[EventLogEntry]:
        return self._instance.get_latest_materialization_event(key)

    @cached_method
    def _get_current_logical_version_provenance(
        self, *, key: AssetKey
    ) -> Optional[LogicalVersionProvenance]:
        materialization = self._get_latest_materialization_event(key=key)
        if materialization is None:
            return None
        else:
            return extract_logical_version_provenance_from_entry(materialization)

    # Returns true if the current logical version of at least one input asset differs from the
    # recorded logical version for that asset in the provenance. This indicates that a new
    # materialization with up-to-date data would produce a different logical verson.
    def _is_provenance_stale(self, key: AssetKey, provenance: LogicalVersionProvenance) -> bool:
        if self._has_updated_dependencies(key=key):
            return True
        else:
            for k, v in provenance.input_logical_versions.items():
                if self._get_projected_logical_version(key=k) != v:
                    return True
            return False

    @cached_method
    def _has_updated_dependencies(self, *, key: AssetKey) -> bool:
        provenance = self._get_current_logical_version_provenance(key=key)
        if provenance is None:
            return True
        else:
            curr_dep_keys = self.asset_graph.get_parents(key)
            old_dep_keys = set(provenance.input_logical_versions.keys())
            return curr_dep_keys != old_dep_keys

    def _compute_projected_new_materialization_logical_version(
        self, key: AssetKey
    ) -> LogicalVersion:
        dep_keys = self.asset_graph.get_parents(key)
        return compute_logical_version(
            self.asset_graph.get_code_version(key) or UNKNOWN_VALUE,
            {dep_key: self._get_projected_logical_version(key=dep_key) for dep_key in dep_keys},
        )
