from typing import Any, Mapping

from dagster import OpExecutionContext
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli, DbtManifest

from . import MANIFEST_PATH


class CustomizedDbtManifest(DbtManifest):
    @classmethod
    def node_info_to_description(cls, node_info: Mapping[str, Any]) -> str:
        description_sections = []

        description = node_info.get("description", "")
        if description:
            description_sections.append(description)

        compiled_code = node_info.get("compiled_code", "")
        if compiled_code:
            description_sections.append(f"#### Compiled SQL:\n```\n{compiled_code}\n```")

        return "\n\n".join(description_sections)


manifest = CustomizedDbtManifest.read(path=MANIFEST_PATH)


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], manifest=manifest, context=context).stream()
