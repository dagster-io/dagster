from typing import Literal, Optional, Sequence

from dagster import AssetExecutionContext, Definitions, asset
from dagster_yaml.definition_set_config import DefinitionSetConfig


class ShellAssetDefinitionConfig(DefinitionSetConfig):
    type: Literal["shell_asset"]
    key: str
    command: str
    deps: Optional[Sequence[str]] = None
    subprocess_client_resource_key: str = "subprocess_client"

    def build_defs(self) -> Definitions:
        @asset(
            key=self.key,
            deps=self.deps,
            required_resource_keys={self.subprocess_client_resource_key},
        )
        def _asset(context: AssetExecutionContext) -> None:
            subprocess_client = getattr(context.resources, self.subprocess_client_resource_key)
            return subprocess_client.run(
                context=context, command=self.command.split(" ")
            ).get_results()

        return Definitions(assets=[_asset])
