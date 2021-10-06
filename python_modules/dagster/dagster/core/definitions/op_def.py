from .solid import SolidDefinition


class OpDefinition(SolidDefinition):
    @property
    def node_type_str(self) -> str:
        return "op"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True
