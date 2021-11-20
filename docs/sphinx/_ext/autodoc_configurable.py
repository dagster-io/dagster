import json
import textwrap
from typing import Any, Optional
from dagster.core.definitions.configurable import ConfigurableDefinition
from dagster.config.config_type import ConfigTypeKind
from dagster import StringSource, IntSource, BoolSource
from sphinx.ext.autodoc import DataDocumenter


def type_repr(config_type):
    if config_type.given_name:
        return config_type.given_name
    if config_type == StringSource:
        return "dagster.StringSource"
    if config_type == StringSource:
        return "dagster.BoolSource"
    if config_type == BoolSource:
        return "dagster.BoolSource"
    if config_type.kind == ConfigTypeKind.ANY:
        return "Any"
    elif config_type.kind == ConfigTypeKind.SCALAR:
        return config_type.scalar_kind.name.lower()
    elif config_type.kind == ConfigTypeKind.ENUM:
        return "Enum{" + ", ".join(str(val) for val in config_type.config_values) + "}"
    elif config_type.kind == ConfigTypeKind.ARRAY:
        return "[{}]".format(type_repr(config_type.inner_type))
    # TODO not sure what to do for this one
    elif config_type.kind == ConfigTypeKind.SELECTOR:
        return "selector"
    elif config_type.kind == ConfigTypeKind.STRICT_SHAPE:
        return "strict dict"
    elif config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        return "permissive dict"
    elif config_type.kind == ConfigTypeKind.SCALAR_UNION:
        # TODO: not sure what to do for the `non_scalar_schema` here-- why not a non scalar type?
        return (
            f"Union[{type_repr(config_type.scalar_type)}, {type_repr(config_type.non_scalar_type)}]"
        )
    elif config_type.kind == ConfigTypeKind.NONEABLE:
        return f"Union[{type_repr(config_type.inner_type)}, None]"


def config_field_to_lines(field, name=None):
    lines = [""]

    if name:
        type_str = type_repr(field.config_type)
        if not field.is_required:
            type_str += ", optional"
        lines.append(f":{name} ({type_str}):")
        if field.description:
            lines.append(f"    {field.description}")
        if field.default_provided:
            val = field.default_value
            if isinstance(val, dict):
                ls = json.dumps(val, indent=4).split("\n")
                lines.append("")
                if len(ls) > 0:
                    lines.append("    .. collapse:: Default Value:")
                    lines.append("")
                    lines.append(" " * 8 + ".. code-block:: javascript")
                    lines.append("")
                    for l in ls:
                        lines.append(" " * 12 + l)
                else:
                    lines.append("    **Default Value:**")
                    lines.append("")
                    lines.append(" " * 4 + ".. code-block:: javascript")
                    lines.append("")
                    for l in ls:
                        lines.append(" " * 8 + l)
            else:
                lines.append("")
                lines.append(f"    **Default Value:** {repr(val)}")

    if hasattr(field.config_type, "fields") and len(field.config_type.fields) > 0:
        lines.append("")
        lines.append("    .. collapse:: Config Schema:")
        for name, subfield in field.config_type.fields.items():
            lines += ["    " + line for line in config_field_to_lines(subfield, name=name)]

    return ["    " + line for line in lines]


class ConfigurableDocumenter(DataDocumenter):
    objtype = "configurable"
    directivetype = "data"

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Any) -> bool:
        return isinstance(member, ConfigurableDefinition)

    def add_content(self, more_content, no_docstring: bool = False) -> None:
        super().add_content(more_content, no_docstring)
        source_name = self.get_sourcename()
        self.add_line("", source_name)

        lines = config_field_to_lines(self.object.config_schema.as_field())
        lines = textwrap.dedent("\n".join(lines)).split("\n")
        for line in lines[:300]:
            print(line)

        for line in lines:
            self.add_line(line, source_name)

        self.add_line("", source_name)
        self.add_line("", source_name)


def setup(app):
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_autodocumenter(ConfigurableDocumenter)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def foo():
    import json
    from dagster_dbt import dbt_cloud_resource, dbt_cli_resource, dbt_rpc_sync_resource

    x = config_field_to_dict(dbt_cloud_resource.config_schema.as_field())
    print(json.dumps(x, indent=4))
    x = config_field_to_dict(dbt_cli_resource.config_schema.as_field())
    print(json.dumps(x, indent=4))
    x = config_field_to_dict(dbt_rpc_sync_resource.config_schema.as_field())
    print(json.dumps(x, indent=4))
