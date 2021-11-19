from typing import Any, Optional
from dagster.core.definitions.configurable import ConfigurableDefinition
from sphinx.ext.autodoc import DataDocumenter


def config_field_to_dict(field):
    d = {}
    if hasattr(field, "fields"):
        for name, subfield in field.config_type.fields.items():
            d[name] = config_field_to_dict(subfield)
    if field.description:
        d["description"] = field.description
    if field.default_provided:
        d["default_value"] = field.default_value

    return d


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

        self.add_line(repr(self.object.config_schema.as_field().config_type.fields), source_name)
        config_type = self.object.config_schema.as_field().config_type
        for name, field in config_type.fields.items():
            self.add_line(f"**{name}** ({field.config_type})", source_name)

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
    from dagster_dbt import dbt_cli_resource

    x = config_field_to_dict(dbt_cli_resource.config_schema.as_field())
    print(json.dumps(x, indent=4))


foo()
