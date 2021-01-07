from collections import namedtuple

from dagster import check
from dagster.core.definitions.dependency import SolidHandle
from dagster.serdes import whitelist_for_serdes


@whitelist_for_serdes
class StepHandle(namedtuple("_StepHandle", "solid_handle")):
    def __new__(cls, solid_handle):
        return super(StepHandle, cls).__new__(
            cls, solid_handle=check.inst_param(solid_handle, "solid_handle", SolidHandle),
        )

    def to_key(self):
        return f"{self.solid_handle.to_string()}"

    @staticmethod
    def from_key(string):
        return StepHandle(SolidHandle.from_string(string))
