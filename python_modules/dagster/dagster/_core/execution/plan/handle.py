import re
from typing import NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions.dependency import NodeHandle
from dagster._serdes import whitelist_for_serdes


# Serialize node_handle -> solid_handle for backcompat
@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
class StepHandle(NamedTuple("_StepHandle", [("node_handle", NodeHandle), ("key", str)])):
    """A reference to an ExecutionStep that was determined statically."""

    def __new__(cls, node_handle: NodeHandle, key: Optional[str] = None):
        return super().__new__(
            cls,
            node_handle=check.inst_param(node_handle, "node_handle", NodeHandle),
            # mypy can't tell that if default is set, this is guaranteed to be a str
            key=cast("str", check.opt_str_param(key, "key", default=str(node_handle))),
        )

    def to_key(self) -> str:
        return self.key

    @staticmethod
    def parse_from_key(
        string: str,
    ) -> Union["StepHandle", "ResolvedFromDynamicStepHandle", "UnresolvedStepHandle"]:
        unresolved_match = re.match(r"(.*)\[\?\]", string)
        if unresolved_match:
            return UnresolvedStepHandle(NodeHandle.from_string(unresolved_match.group(1)))

        resolved_match = re.match(r"(.*)\[(.*)\]", string)
        if resolved_match:
            return ResolvedFromDynamicStepHandle(
                NodeHandle.from_string(resolved_match.group(1)), resolved_match.group(2)
            )

        return StepHandle(NodeHandle.from_string(string))


# Serialize node_handle -> solid_handle for backcompat
@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
class UnresolvedStepHandle(NamedTuple("_UnresolvedStepHandle", [("node_handle", NodeHandle)])):
    """A reference to an UnresolvedMappedExecutionStep in an execution."""

    def __new__(cls, node_handle: NodeHandle):
        return super().__new__(
            cls,
            node_handle=check.inst_param(node_handle, "node_handle", NodeHandle),
        )

    def to_key(self) -> str:
        return f"{self.node_handle}[?]"

    def resolve(self, map_key) -> "ResolvedFromDynamicStepHandle":
        return ResolvedFromDynamicStepHandle(self.node_handle, map_key)


# Serialize node_handle -> solid_handle for backcompat
@whitelist_for_serdes(storage_field_names={"node_handle": "solid_handle"})
class ResolvedFromDynamicStepHandle(
    NamedTuple(
        "_ResolvedFromDynamicStepHandle",
        [("node_handle", NodeHandle), ("mapping_key", str), ("key", str)],
    )
):
    """A reference to an ExecutionStep that came from resolving an UnresolvedMappedExecutionStep
    (and associated UnresolvedStepHandle) downstream of a dynamic output after it has
    completed successfully.
    """

    def __new__(cls, node_handle: NodeHandle, mapping_key: str, key: Optional[str] = None):
        return super().__new__(
            cls,
            node_handle=check.inst_param(node_handle, "node_handle", NodeHandle),
            mapping_key=check.str_param(mapping_key, "mapping_key"),
            # mypy can't tell that if default is set, this is guaranteed to be a str
            key=cast(
                "str",
                check.opt_str_param(key, "key", default=f"{node_handle}[{mapping_key}]"),
            ),
        )

    def to_key(self) -> str:
        return self.key

    @property
    def unresolved_form(self) -> UnresolvedStepHandle:
        return UnresolvedStepHandle(node_handle=self.node_handle)
