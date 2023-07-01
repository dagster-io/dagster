import inspect
import json
import textwrap
from typing import Any, List, Tuple, Type, Union, cast

import dagster._check as check
import docutils.nodes
from dagster import BoolSource, Field, IntSource, StringSource
from dagster._annotations import is_deprecated, is_public
from dagster._config.config_type import (
    Array,
    ConfigScalar,
    ConfigType,
    ConfigTypeKind,
    Enum,
    Noneable,
    ScalarUnion,
)
from dagster._config.pythonic_config import (
    ConfigurableResource,
    ConfigurableResourceFactory,
    infer_schema_from_config_class,
)
from dagster._core.definitions.configurable import ConfigurableDefinition
from dagster._serdes import ConfigurableClass
from sphinx.addnodes import versionmodified
from sphinx.ext.autodoc import ClassDocumenter, DataDocumenter, ObjectMembers


def type_repr(config_type: ConfigType) -> str:
    """Generate a human-readable name for a given dagster ConfigType."""
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
        config_type = cast(ConfigScalar, config_type)
        return config_type.scalar_kind.name.lower()
    elif config_type.kind == ConfigTypeKind.ENUM:
        config_type = cast(Enum, config_type)
        return "Enum{" + ", ".join(str(val) for val in config_type.config_values) + "}"
    elif config_type.kind == ConfigTypeKind.ARRAY:
        config_type = cast(Array, config_type)
        return f"List[{type_repr(config_type.inner_type)}]"
    elif config_type.kind == ConfigTypeKind.SELECTOR:
        return "selector"
    elif config_type.kind == ConfigTypeKind.STRICT_SHAPE:
        return "strict dict"
    elif config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        return "permissive dict"
    elif config_type.kind == ConfigTypeKind.MAP:
        return "dict"
    elif config_type.kind == ConfigTypeKind.SCALAR_UNION:
        config_type = cast(ScalarUnion, config_type)
        return (
            f"Union[{type_repr(config_type.scalar_type)}, {type_repr(config_type.non_scalar_type)}]"
        )
    elif config_type.kind == ConfigTypeKind.NONEABLE:
        config_type = cast(Noneable, config_type)
        return f"Union[{type_repr(config_type.inner_type)}, None]"
    else:
        raise Exception(f"Unhandled config type {config_type}")


def config_field_to_lines(field, name=None) -> List[str]:
    """Given a config field, turn it into a list of lines to add to the documentation."""
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
            for ln in field.description.split("\n"):
                # escape '*' characters because they get interpreted as emphasis markers in rst
                lines.append(" " * 4 + textwrap.dedent(ln.replace("*", "\\*")))
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
                for ln in ls:
                    lines.append(" " * 12 + ln)
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
    def can_document_member(
        cls, member: Any, _membername: str, _isattr: bool, _parent: Any
    ) -> bool:
        return (
            isinstance(member, ConfigurableDefinition)
            or isinstance(member, type)
            and issubclass(member, ConfigurableClass)
        )

    def add_content(self, more_content) -> None:
        source_name = self.get_sourcename()
        self.add_line("", source_name)
        # explicit visual linebreak
        self.add_line("|", source_name)
        self.add_line("", source_name)

        if inspect.isfunction(self.object):
            # self.object is a function that returns a configurable class eg build_snowflake_io_manager
            obj = self.object([])
        else:
            obj = self.object

        obj = cast(
            Union[ConfigurableDefinition, Type[ConfigurableClass], ConfigurableResource], obj
        )

        config_field = None
        if isinstance(obj, ConfigurableDefinition):
            config_field = check.not_none(obj.config_schema).as_field()
        elif inspect.isclass(obj) and (
            issubclass(obj, ConfigurableResource) or issubclass(obj, ConfigurableResourceFactory)
        ):
            config_field = infer_schema_from_config_class(obj)
        elif isinstance(obj, type) and issubclass(obj, ConfigurableClass):
            config_field = Field(obj.config_type())

        for line in config_field_to_lines(config_field):
            self.add_line(line, source_name)

        self.add_line("", source_name)
        # do this call at the bottom so that config schema is first thing in documentation
        super().add_content(more_content)


class DagsterClassDocumenter(ClassDocumenter):
    """Overrides the default autodoc ClassDocumenter to adds some extra options."""

    objtype = "class"

    option_spec = ClassDocumenter.option_spec.copy()
    option_spec["deprecated_aliases"] = lambda string: [s.strip() for s in string.split(",")]

    def add_content(self, *args, **kwargs):
        super().add_content(*args, **kwargs)
        source_name = self.get_sourcename()
        for alias in self.options.get("deprecated_aliases", []):
            self.add_line(f"ALIAS: {alias}", source_name)

    def get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]:
        _, unfiltered_members = super().get_object_members(want_all)
        # Use form `is_public(self.object, attr_name) if possible, because to access a descriptor
        # object (returned by e.g. `@staticmethod`) you need to go in through
        # `self.object.__dict__`-- the value provided in the member list is _not_ the descriptor!
        return False, [
            m
            for m in unfiltered_members
            if (m[0] in self.object.__dict__ and is_public(self.object, m[0]) or is_public(m[1]))
        ]


# This is a hook that will be executed for every processed docstring. It modifies the lines of the
# docstring in place.
def process_docstring(app, what, name, obj, options, lines):
    # Insert a "deprecated" sphinx directive (this is built-in to autodoc) for objects flagged with
    # @deprecated.
    if is_deprecated(obj):
        # Note that these are in reversed order from how they will appear because we insert at the
        # front. We insert the <placeholder> string because the directive requires an argument that
        # we can't supply (we would have to know the version at which the object was deprecated).
        # We discard the "<placeholder>" string in `substitute_deprecated_text`.
        for line in ["", ".. deprecated:: <placeholder>"]:
            lines.insert(0, line)


def substitute_deprecated_text(app, doctree, fromdocname):
    # The `.. deprecated::` directive is rendered as a `versionmodified` node.
    # Find them all and replace the auto-generated text, which requires a version argument, with a
    # plain string "Deprecated".
    for node in doctree.findall(versionmodified):
        paragraph = node.children[0]
        inline = paragraph.children[0]
        text = inline.children[0]
        inline.replace(text, docutils.nodes.Text("Deprecated"))


def setup(app):
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_autodocumenter(ConfigurableDocumenter)
    # override allows `.. autoclass::` to invoke DagsterClassDocumenter instead of default
    app.add_autodocumenter(DagsterClassDocumenter, override=True)
    app.connect("autodoc-process-docstring", process_docstring)
    app.connect("doctree-resolved", substitute_deprecated_text)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
