from .solid import SolidDefinition


class OpDefinition(SolidDefinition):
    @property
    def node_type_str(self) -> str:
        return "op"
