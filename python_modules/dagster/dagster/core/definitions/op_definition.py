from typing import Dict

from .input import In
from .output import Out
from .solid_definition import SolidDefinition


class OpDefinition(SolidDefinition):
    @property
    def node_type_str(self) -> str:
        return "op"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @property
    def ins(self) -> Dict[str, In]:
        return {input_def.name: In.from_definition(input_def) for input_def in self.input_defs}

    @property
    def outs(self) -> Dict[str, Out]:
        return {output_def.name: Out.from_definition(output_def) for output_def in self.output_defs}
