from typing import Any, Mapping

from dagster import OpExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
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


@dbt_assets(manifest=MANIFEST_PATH, dagster_dbt_translator=CustomDagsterDbtTranslator())
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], context=context).stream()
