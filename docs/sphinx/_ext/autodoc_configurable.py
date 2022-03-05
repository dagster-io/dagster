import json
import textwrap
from typing import Any, List

from dagster import BoolSource, Field, IntSource, StringSource
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.core.definitions.configurable import ConfigurableDefinition
from dagster.serdes import ConfigurableClass
from sphinx.ext.autodoc import DataDocumenter   # pylint: disable=import-error,no-name-in-module


def type_repr(config_type: ConfigType) -> str:
    """Generate a human-readable name for a given dagster ConfigType"""

    # Use given name if possible
    if config_type.given_name:
        return config_type.given_name

    # The xSource types are a particular kind of selector that is very common, special case these
    if config_type == StringSource:
        return "dagster.StringSource"
    elif config_type == BoolSource:
        return "dagster.BoolSource"
    elif config_type == IntSource:
        return "dagster.IntSource"
    elif config_type.kind == ConfigTypeKind.ANY:
        return "Any"
    elif config_type.kind == ConfigTypeKind.SCALAR:
        return config_type.scalar_kind.name.lower()
    elif config_type.kind == ConfigTypeKind.ENUM:
        return "Enum{" + ", ".join(str(val) for val in config_type.config_values) + "}"
    elif config_type.kind == ConfigTypeKind.ARRAY:
        return "List[{}]".format(type_repr(config_type.inner_type))
    elif config_type.kind == ConfigTypeKind.SELECTOR:
        return "selector"
    elif config_type.kind == ConfigTypeKind.STRICT_SHAPE:
        return "strict dict"
    elif config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        return "permissive dict"
    elif config_type.kind == ConfigTypeKind.SCALAR_UNION:
        return (
            f"Union[{type_repr(config_type.scalar_type)}, {type_repr(config_type.non_scalar_type)}]"
        )
    elif config_type.kind == ConfigTypeKind.NONEABLE:
        return f"Union[{type_repr(config_type.inner_type)}, None]"


def config_field_to_lines(field, name=None) -> List[str]:
    """Given a config field, turn it into a list of lines to add to the documentation"""
    lines = [""]

    # The only unnamed field will be the top level config schema wrapper
    if name:
        type_str = type_repr(field.config_type)
        if not field.is_required:
            type_str += ", optional"
        lines.append(f":{name} ({type_str}):")
        if field.description:
            # trim / normalize whitespace. some of our config descriptions misuse triple-quote blocks
            # so this makes them look nicer
            for l in field.description.split("\n"):
                # escape '*' characters because they get interpreted as emphasis markers in rst
                lines.append(" " * 4 + textwrap.dedent(l.replace("*", "\\*")))
            lines.append("")

        if field.default_provided:
            val = field.default_value
            # for fields with dictionary default vals, hide them in collapsible block
            if isinstance(val, dict):
                ls = json.dumps(val, indent=4).split("\n")
                lines.append("")
                lines.append("    .. collapse:: Default Value:")
                lines.append("")
                lines.append("        .. code-block:: javascript")
                lines.append("")
                for l in ls:
                    lines.append(" " * 12 + l)
            else:
                lines.append("")
                lines.append(f"    **Default Value:** {repr(val)}")

    # if field has subfields, recurse
    if hasattr(field.config_type, "fields") and len(field.config_type.fields) > 0:
        lines.append("")
        # for the top level, no need to indent
        indent = "    " if name else ""
        lines.append(indent + ".. collapse:: Config Schema:")
        for name, subfield in field.config_type.fields.items():
            # indent all of these lines to fit under the collapse block
            lines += [indent + "    " + line for line in config_field_to_lines(subfield, name=name)]

    return lines


class ConfigurableDocumenter(DataDocumenter):
    objtype = "configurable"
    directivetype = "data"

    @classmethod
    def can_document_member(cls, member: Any, _membername: str, _isattr: bool, _parent: Any) -> bool:
        return isinstance(member, ConfigurableDefinition) or isinstance(member, ConfigurableClass)

    def add_content(self, more_content, no_docstring: bool = False) -> None:
        source_name = self.get_sourcename()
        self.add_line("", source_name)
        # explicit visual linebreak
        self.add_line("|", source_name)
        self.add_line("", source_name)

        if isinstance(self.object, ConfigurableDefinition):
            config_field = self.object.config_schema.as_field()
        elif issubclass(self.object, ConfigurableClass):
            config_field = Field(self.object.config_type())
        for line in config_field_to_lines(config_field):
            self.add_line(line, source_name)

        self.add_line("", source_name)
        # do this call at the bottom so that config schema is first thing in documentation
        super().add_content(more_content, no_docstring)


def setup(app):
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_autodocumenter(ConfigurableDocumenter)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
