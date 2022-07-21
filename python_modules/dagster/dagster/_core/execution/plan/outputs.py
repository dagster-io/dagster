from typing import List, NamedTuple, Optional, Union

import dagster._check as check
from dagster._core.definitions import (
    AssetMaterialization,
    Materialization,
    MetadataEntry,
    NodeHandle,
)
from dagster._core.definitions.events import AssetKey
from dagster._serdes import whitelist_for_serdes

from .handle import UnresolvedStepHandle
from .objects import TypeCheckData


@whitelist_for_serdes
class StepOutputProperties(
    NamedTuple(
        "_StepOutputProperties",
        [
            ("is_required", bool),
            ("is_dynamic", bool),
            ("is_asset", bool),
            ("should_materialize", bool),
            ("asset_key", Optional[AssetKey]),
        ],
    )
):
    def __new__(
        cls,
        is_required: bool,
        is_dynamic: bool,
        is_asset: bool,
        should_materialize: bool,
        asset_key: Optional[AssetKey] = None,
    ):
        return super(StepOutputProperties, cls).__new__(
            cls,
            check.bool_param(is_required, "is_required"),
            check.bool_param(is_dynamic, "is_dynamic"),
            check.bool_param(is_asset, "is_asset"),
            check.bool_param(should_materialize, "should_materialize"),
            check.opt_inst_param(asset_key, "asset_key", AssetKey),
        )


class StepOutput(
    NamedTuple(
        "_StepOutput",
        [
            ("solid_handle", NodeHandle),
            ("name", str),
            ("dagster_type_key", str),
            ("properties", StepOutputProperties),
        ],
    )
):
    """Holds the information for an ExecutionStep to process its outputs"""

    def __new__(
        cls,
        solid_handle: NodeHandle,
        name: str,
        dagster_type_key: str,
        properties: StepOutputProperties,
    ):
        return super(StepOutput, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", NodeHandle),
            name=check.str_param(name, "name"),
            dagster_type_key=check.str_param(dagster_type_key, "dagster_type_key"),
            properties=check.inst_param(properties, "properties", StepOutputProperties),
        )

    @property
    def is_required(self) -> bool:
        return self.properties.is_required

    @property
    def is_dynamic(self) -> bool:
        return self.properties.is_dynamic

    @property
    def is_asset(self) -> bool:
        return self.properties.is_asset

    @property
    def should_materialize(self) -> bool:
        return self.properties.should_materialize

    @property
    def asset_key(self) -> Optional[AssetKey]:
        if not self.is_asset:
            return None
        return self.properties.asset_key


@whitelist_for_serdes
class StepOutputData(
    NamedTuple(
        "_StepOutputData",
        [
            ("step_output_handle", "StepOutputHandle"),
            ("type_check_data", Optional[TypeCheckData]),
            ("version", Optional[str]),
            ("metadata_entries", Optional[List[MetadataEntry]]),
        ],
    )
):
    """Serializable payload of information for the result of processing a step output"""

    def __new__(
        cls,
        step_output_handle: "StepOutputHandle",
        type_check_data: Optional[TypeCheckData] = None,
        version: Optional[str] = None,
        metadata_entries: Optional[List[MetadataEntry]] = None,
        # graveyard
        # pylint: disable=unused-argument
        intermediate_materialization: Optional[Union[AssetMaterialization, Materialization]] = None,
    ):
        return super(StepOutputData, cls).__new__(
            cls,
            step_output_handle=check.inst_param(
                step_output_handle, "step_output_handle", StepOutputHandle
            ),
            type_check_data=check.opt_inst_param(type_check_data, "type_check_data", TypeCheckData),
            version=check.opt_str_param(version, "version"),
            metadata_entries=check.opt_list_param(
                metadata_entries, "metadata_entries", MetadataEntry
            ),
        )

    @property
    def output_name(self) -> str:
        return self.step_output_handle.output_name

    @property
    def mapping_key(self) -> Optional[str]:
        return self.step_output_handle.mapping_key


@whitelist_for_serdes
class StepOutputHandle(
    NamedTuple(
        "_StepOutputHandle",
        [("step_key", str), ("output_name", str), ("mapping_key", Optional[str])],
    )
):
    """A reference to a specific output that has or will occur within the scope of an execution"""

    def __new__(cls, step_key: str, output_name: str = "result", mapping_key: Optional[str] = None):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step_key=check.str_param(step_key, "step_key"),
            output_name=check.str_param(output_name, "output_name"),
            mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
        )


@whitelist_for_serdes
class UnresolvedStepOutputHandle(
    NamedTuple(
        "_UnresolvedStepOutputHandle",
        [
            ("unresolved_step_handle", UnresolvedStepHandle),
            ("output_name", str),
            ("resolved_by_step_key", str),
            ("resolved_by_output_name", str),
        ],
    )
):
    """
    Placeholding that will resolve to StepOutputHandle for each mapped output once the
    upstream dynamic step has completed.
    """

    def __new__(
        cls,
        unresolved_step_handle: UnresolvedStepHandle,
        output_name: str,
        resolved_by_step_key: str,
        resolved_by_output_name: str,
    ):
        return super(UnresolvedStepOutputHandle, cls).__new__(
            cls,
            unresolved_step_handle=check.inst_param(
                unresolved_step_handle, "unresolved_step_handle", UnresolvedStepHandle
            ),
            output_name=check.str_param(output_name, "output_name"),
            # this could be a set of resolution keys to support multiple mapping operations
            resolved_by_step_key=check.str_param(resolved_by_step_key, "resolved_by_step_key"),
            resolved_by_output_name=check.str_param(
                resolved_by_output_name, "resolved_by_output_name"
            ),
        )

    def resolve(self, map_key) -> StepOutputHandle:
        """Return a resolved StepOutputHandle"""
        return StepOutputHandle(
            self.unresolved_step_handle.resolve(map_key).to_key(), self.output_name
        )

    def get_step_output_handle_with_placeholder(self) -> StepOutputHandle:
        """Return a StepOutputHandle with a unresolved step key as a placeholder"""
        return StepOutputHandle(self.unresolved_step_handle.to_key(), self.output_name)
