import re
from typing import List, NamedTuple, Optional, Sequence, Union, cast

import dagster._check as check
from dagster._core.definitions.dependency import NodeHandle
from dagster._serdes import whitelist_for_serdes
from dagster._utils import frozenlist


@whitelist_for_serdes
class StepHandle(NamedTuple("_StepHandle", [("solid_handle", NodeHandle), ("key", str)])):
    """A reference to an ExecutionStep that was determined statically"""

    def __new__(cls, solid_handle: NodeHandle, key: Optional[str] = None):
        return super(StepHandle, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", NodeHandle),
            # mypy can't tell that if default is set, this is guaranteed to be a str
            key=cast(str, check.opt_str_param(key, "key", default=solid_handle.to_string())),
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


@whitelist_for_serdes
class UnresolvedStepHandle(
    NamedTuple(
        "_UnresolvedStepHandle",
        [
            ("solid_handle", NodeHandle),
            ("partial_keys", frozenlist),
        ],
    ),
):
    """A reference to an UnresolvedMappedExecutionStep in an execution"""

    def __new__(
        cls,
        solid_handle: NodeHandle,
        partial_keys: Optional[Sequence[str]] = None,
    ):
        return super(UnresolvedStepHandle, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", NodeHandle),
            partial_keys=frozenlist(check.opt_sequence_param(partial_keys, "partial_keys")),
        )

    def to_key(self):
        # prototype note: should we have "?" repeated
        keys = [*self.partial_keys, "?"]
        return f"{self.solid_handle.to_string()}[{','.join(keys)}]"

    def resolve(self, map_key) -> "ResolvedFromDynamicStepHandle":
        # map_key 
        return ResolvedFromDynamicStepHandle(self.solid_handle, [*self.partial_keys, map_key])

    def partial_resolve(self, map_key):
        # map_key array or single
        return UnresolvedStepHandle(self.solid_handle, partial_keys=[*self.partial_keys, map_key])


@whitelist_for_serdes
class ResolvedFromDynamicStepHandle(
    NamedTuple(
        "_ResolvedFromDynamicStepHandle",
        [("solid_handle", NodeHandle), ("mapping_key", str), ("key", str)],
    )
):
    """
    A reference to an ExecutionStep that came from resolving an UnresolvedMappedExecutionStep
    (and associated UnresolvedStepHandle) downstream of a dynamic output after it has
    completed successfully.
    """

    def __new__(
        cls,
        solid_handle: NodeHandle,
        mapping_key: Union[str, List[str]],
        key: Optional[str] = None,
    ):
        if isinstance(mapping_key, list):
            mapping_key = ",".join(mapping_key)
        return super(ResolvedFromDynamicStepHandle, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", NodeHandle),
            mapping_key=check.str_param(mapping_key, "mapping_key"),
            # mypy can't tell that if default is set, this is guaranteed to be a str
            key=cast(
                str,
                check.opt_str_param(
                    key, "key", default=f"{solid_handle.to_string()}[{mapping_key}]"
                ),
            ),
        )

    def to_key(self) -> str:
        return self.key

    @property
    def unresolved_form(self) -> UnresolvedStepHandle:
        return UnresolvedStepHandle(solid_handle=self.solid_handle)
