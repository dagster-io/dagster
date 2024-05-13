from typing import Generic, Literal, Sequence, TypeVar

from dagster import Definitions

from dagster_yaml.definition_set_config import DefinitionSetConfig

T_DefinitionSetConfig = TypeVar("T_DefinitionSetConfig", bound=DefinitionSetConfig)


class MultiDefinitionSetConfig(DefinitionSetConfig, Generic[T_DefinitionSetConfig]):
    type: Literal["multi"]
    defs: Sequence[T_DefinitionSetConfig]

    def build_defs(self) -> Definitions:
        def_sets = [defs.build_defs() for defs in self.defs]
        return Definitions.merge(*def_sets)
