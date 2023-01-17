from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence, Union

from typing_extensions import Final

from dagster import _check as check
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.definitions.events import (
        AssetKey,
        AssetMaterialization,
        AssetObservation,
        Materialization,
    )
    from dagster._core.events.log import EventLogEntry
    from dagster._core.host_representation.external import ExternalRepository
    from dagster._core.host_representation.external_data import ExternalAssetNode
    from dagster._core.instance import DagsterInstance


class UnknownValue:
    pass


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


UNKNOWN_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("UNKNOWN")
DEFAULT_LOGICAL_VERSION: Final[LogicalVersion] = LogicalVersion("INITIAL")


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
# ##### PROJECTED LOGICAL VERSION LOADER
# ########################


class CachingProjectedLogicalVersionResolver:
    """
    Used to resolve a set of projected logical versions with caching. Avoids redundant database
    calls that would occur when naively iteratively computing projected logical versions without caching.
    """

    def __init__(
        self,
        instance: "DagsterInstance",
        repositories: Sequence["ExternalRepository"],
        key_to_node_map: Optional[Mapping[AssetKey, "ExternalAssetNode"]],
    ):
        self._instance = instance
        self._key_to_node_map = check.opt_mapping_param(key_to_node_map, "key_to_node_map")
        self._repositories = repositories

    def get(self, asset_key: AssetKey) -> LogicalVersion:
        return self._get_version(key=asset_key)

    @cached_method
    def _get_version(self, *, key: AssetKey) -> LogicalVersion:
        node = self._fetch_node(key)
        if node.is_source:
            event = self._instance.get_latest_logical_version_record(key, True)
            if event:
                version = (
                    extract_logical_version_from_entry(event.event_log_entry)
                    or DEFAULT_LOGICAL_VERSION
                )
            else:
                version = DEFAULT_LOGICAL_VERSION
        elif node.code_version is not None:
            version = self._compute_projected_new_materialization_logical_version(node)
        else:
            materialization = self._instance.get_latest_materialization_event(key)
            if materialization is None:  # never been materialized
                version = self._compute_projected_new_materialization_logical_version(node)
            else:
                logical_version = extract_logical_version_from_entry(materialization)
                provenance = extract_logical_version_provenance_from_entry(materialization)
                if (
                    logical_version is None  # old materialization event before logical versions
                    or provenance is None  # should never happen
                    or self._is_provenance_stale(node, provenance)
                ):
                    version = self._compute_projected_new_materialization_logical_version(node)
                else:
                    version = logical_version
        return version

    # Returns true if the current logical version of at least one input asset differs from the
    # recorded logical version for that asset in the provenance. This indicates that a new
    # materialization with up-to-date data would produce a different logical verson.
    def _is_provenance_stale(
        self, node: "ExternalAssetNode", provenance: LogicalVersionProvenance
    ) -> bool:
        if self._has_updated_dependencies(node, provenance):
            return True
        else:
            for k, v in provenance.input_logical_versions.items():
                if self._get_version(key=k) != v:
                    return True
            return False

    def _has_updated_dependencies(
        self, node: "ExternalAssetNode", provenance: LogicalVersionProvenance
    ) -> bool:
        curr_dep_keys = {dep.upstream_asset_key for dep in node.dependencies}
        old_dep_keys = set(provenance.input_logical_versions.keys())
        return curr_dep_keys != old_dep_keys

    def _compute_projected_new_materialization_logical_version(
        self, node: "ExternalAssetNode"
    ) -> LogicalVersion:
        dep_keys = {dep.upstream_asset_key for dep in node.dependencies}
        return compute_logical_version(
            node.code_version or UNKNOWN_VALUE,
            {dep_key: self._get_version(key=dep_key) for dep_key in dep_keys},
        )

    def _fetch_node(self, key: AssetKey) -> "ExternalAssetNode":
        if key in self._key_to_node_map:
            return self._key_to_node_map[key]
        else:
            self._fetch_all_nodes()
            return self._fetch_node(key)

    def _fetch_all_nodes(self) -> None:
        self._key_to_node_map = {}
        for repository in self._repositories:
            for node in repository.get_external_asset_nodes():
                self._key_to_node_map[node.asset_key] = node
