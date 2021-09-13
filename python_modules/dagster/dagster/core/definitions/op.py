from .solid import SolidDefinition


class OpDefinition(SolidDefinition):
    @property
    def node_as_str(self) -> str:
        return "op"
