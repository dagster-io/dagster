import re
from typing import NamedTuple, Optional, Union

from dagster import check
from dagster.core.definitions.dependency import SolidHandle
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class StepHandle(NamedTuple("_StepHandle", [("solid_handle", SolidHandle)])):
    """A reference to an ExecutionStep that was determined statically"""

    def __new__(cls, solid_handle: Optional[SolidHandle]):
        return super(StepHandle, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
        )

    def to_key(self) -> str:
        return f"{self.solid_handle.to_string()}"

    @staticmethod
    def parse_from_key(
        string: str,
    ) -> Union["StepHandle", "ResolvedFromDynamicStepHandle", "UnresolvedStepHandle"]:
        unresolved_match = re.match(r"(.*)\[\?\]", string)
        if unresolved_match:
            return UnresolvedStepHandle(SolidHandle.from_string(unresolved_match.group(1)))

        resolved_match = re.match(r"(.*)\[(.*)\]", string)
        if resolved_match:
            return ResolvedFromDynamicStepHandle(
                SolidHandle.from_string(resolved_match.group(1)), resolved_match.group(2)
            )

        return StepHandle(SolidHandle.from_string(string))


class UnresolvedStepHandle(NamedTuple("_UnresolvedStepHandle", [("solid_handle", SolidHandle)])):
    """A reference to an UnresolvedExecutionStep in an execution"""

    def __new__(cls, solid_handle: Optional[SolidHandle]):
        return super(UnresolvedStepHandle, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
        )

    def to_key(self):
        return f"{self.solid_handle.to_string()}[?]"

    def resolve(self, map_key) -> "ResolvedFromDynamicStepHandle":
        return ResolvedFromDynamicStepHandle(self.solid_handle, map_key)


@whitelist_for_serdes
class ResolvedFromDynamicStepHandle(
    NamedTuple(
        "_ResolvedFromDynamicStepHandle", [("solid_handle", SolidHandle), ("mapping_key", str)]
    )
):
    """
    A reference to an ExecutionStep that came from resolving an UnresolvedExecutionStep
    (and associated UnresolvedStepHandle) downstream of a dynamic output after it has
    completed successfully.
    """

    def __new__(cls, solid_handle: Optional[SolidHandle], mapping_key: str):
        return super(ResolvedFromDynamicStepHandle, cls).__new__(
            cls,
            solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
            mapping_key=check.str_param(mapping_key, "mapping_key"),
        )

    def to_key(self) -> str:
        return f"{self.solid_handle.to_string()}[{self.mapping_key}]"

    @property
    def unresolved_form(self) -> UnresolvedStepHandle:
        return UnresolvedStepHandle(solid_handle=self.solid_handle)
