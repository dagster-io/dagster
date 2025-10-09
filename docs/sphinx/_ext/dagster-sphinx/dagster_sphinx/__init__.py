from typing import List, Tuple, Type, TypeVar  # noqa: F401, UP035

import docutils.nodes as nodes
from dagster._annotations import (
    get_beta_info,
    get_beta_params,
    get_deprecated_info,
    get_deprecated_params,
    get_preview_info,
    get_superseded_info,
    has_beta_params,
    has_deprecated_params,
    is_beta,
    is_deprecated,
    is_preview,
    is_public,
    is_superseded,
)
from dagster._record import get_original_class, is_record
from sphinx.application import Sphinx
from sphinx.domains.python import ObjectEntry
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc import (
    ClassDocumenter,
    ObjectMember,
    Options as AutodocOptions,
)
from sphinx.util import logging
from typing_extensions import Literal, TypeAlias

from dagster_sphinx.configurable import ConfigurableDocumenter
from dagster_sphinx.docstring_flags import (
    FlagDirective,
    depart_flag,
    flag,
    inject_object_flag,
    inject_param_flag,
    inline_flag,
    inline_flag_role,
    visit_flag,
    visit_inline_flag,
)

logger = logging.getLogger(__name__)


##### Useful links for Sphinx documentation
#
# [Event reference] https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
#   These events are emitted during the build and can be hooked into during the
#   build process.
# [autodoc] https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
#   Autodoc is not sphinx itself, but it is the central extension that reads
#   docstrings.
# [Sphinx extensions API] https://www.sphinx-doc.org/en/master/extdev/index.html
#   Root page for learning about writing extensions.


# See: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#docstring-preprocessing
# Autodoc doesn't provide it's own alias.
AutodocObjectType: TypeAlias = Literal[
    "module", "class", "exception", "function", "method", "attribute"
]


def record_error(message: str) -> None:
    logger.error(message)
    raise Exception(message)


# ########################
# ##### CHECKS
# ########################


def check_public_method_has_docstring(env: BuildEnvironment, name: str, obj: object) -> None:
    if name != "__init__" and not hasattr(obj, "__doc__"):
        message = (
            f"Docstring not found for {obj!r}.{name}. "
            "All public methods and properties must have docstrings."
        )
        record_error(message)


# Note that in our codebase docstrings with attributes will usually be written as:
#
#     Attributes:
#         attr_name (type): Description
#         ...
#
# Each entry get converted into the rst `..attribute::` directive during preprocessing of
# docstrings, so that's what we check for.
def has_attrs(docstring: list[str]) -> bool:
    return any(line.startswith(".. attribute::") for line in docstring)


class DagsterClassDocumenter(ClassDocumenter):
    """Overrides the default autodoc ClassDocumenter to adds some extra options."""

    objtype = "class"

    def get_object_members(self, want_all: bool) -> tuple[bool, list[ObjectMember]]:
        # the @record transform creates a new outer class, so redirect
        # sphinx to target the original class for scraping members out of __dict__
        if is_record(self.object):
            self.object = get_original_class(self.object)

        _, unfiltered_members = super().get_object_members(want_all)
        # Use form `is_public(self.object, attr_name) if possible, because to access a descriptor
        # object (returned by e.g. `@staticmethod`) you need to go in through
        # `self.object.__dict__`-- the value provided in the member list is _not_ the descriptor!
        filtered_members = [
            m
            for m in unfiltered_members
            if m.__name__ in self.object.__dict__
            and self._is_member_public(self.object.__dict__[m.__name__])
        ]
        for member in filtered_members:
            check_public_method_has_docstring(self.env, member.__name__, member.object)
        return False, filtered_members

    def _is_member_public(self, member: object) -> bool:
        return self.fullname.startswith("dagster_pipes") or is_public(member)


# This is a hook that will be executed for every processed docstring. It modifies the lines of the
# docstring in place.
def process_docstring(
    app: Sphinx,
    what: AutodocObjectType,
    name: str,
    obj: object,
    options: AutodocOptions,
    lines: list[str],
) -> None:
    assert app.env is not None

    if has_attrs(lines):
        record_error(f'Object {name} has "Attributes:" in docstring. Use "Args:" instead.')

    if is_deprecated(obj):
        inject_object_flag(obj, get_deprecated_info(obj), lines)

    if is_superseded(obj):
        inject_object_flag(obj, get_superseded_info(obj), lines)

    if is_preview(obj):
        inject_object_flag(obj, get_preview_info(obj), lines)

    if is_beta(obj):
        inject_object_flag(obj, get_beta_info(obj), lines)

    if has_beta_params(obj):
        params = get_beta_params(obj)
        for param, info in params.items():
            inject_param_flag(lines, param, info)

    if has_deprecated_params(obj):
        params = get_deprecated_params(obj)
        for param, info in params.items():
            inject_param_flag(lines, param, info)


T_Node = TypeVar("T_Node", bound=nodes.Node)


def get_child_as(node: nodes.Node, index: int, node_type: type[T_Node]) -> T_Node:
    child = node.children[index]
    assert isinstance(child, node_type), (
        f"Docutils node not of expected type. Expected `{node_type}`, got `{type(child)}`."
    )
    return child


def transform_inventory_uri(uri: str) -> str:
    """Transform Sphinx source paths to final documentation URLs.

    Transforms paths like:
        sections/api/apidocs/dagster/internals/
    to:
        api/dagster/internals
    """
    # Remove the 'sections/api/apidocs/' prefix
    if uri.startswith("sections/api/apidocs/"):
        transformed = uri.replace("sections/api/apidocs/", "api/", 1)
        # Remove trailing slash if present
        if transformed.endswith("/"):
            transformed = transformed[:-1]
        return transformed
    return uri


def fix_inventory_uris(app: Sphinx, env) -> None:
    """Fix URIs in the Sphinx inventory before it's written.

    This hook runs during env-updated which happens after all documents are read
    and before the build writes output files, allowing us to transform the URIs
    in the domain data.
    """
    if env is None:
        return

    # Access the inventory data from the Python domain
    py_domain = env.domaindata.get("py", {})
    objects = py_domain.get("objects", {})

    # Transform each URI
    # In modern Sphinx (8.x), objects is dict[str, ObjectEntry]
    # ObjectEntry is a namedtuple/dataclass with (docname, node_id, objtype, aliased)
    modified_count = 0
    for name, obj_data in list(objects.items()):
        if isinstance(obj_data, ObjectEntry):
            # New format: ObjectEntry with docname attribute
            old_docname = obj_data.docname
            new_docname = transform_inventory_uri(old_docname)
            if new_docname != old_docname:
                # Create a new ObjectEntry with the transformed docname
                objects[name] = ObjectEntry(
                    docname=new_docname,
                    node_id=obj_data.node_id,
                    objtype=obj_data.objtype,
                    aliased=obj_data.aliased,
                )
                modified_count += 1
        elif isinstance(obj_data, tuple):
            # Old format: (docname, node_id, objtype, aliased)
            docname, node_id, objtype, aliased = obj_data
            new_docname = transform_inventory_uri(docname)
            if new_docname != docname:
                objects[name] = (new_docname, node_id, objtype, aliased)
                modified_count += 1

    if modified_count > 0:
        logger.info(
            f"[dagster_sphinx] Transformed {modified_count} inventory URIs for correct URL structure"
        )


def setup(app):
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_autodocumenter(ConfigurableDocumenter)
    # override allows `.. autoclass::` to invoke DagsterClassDocumenter instead of default
    app.add_autodocumenter(DagsterClassDocumenter, override=True)
    app.add_directive("flag", FlagDirective)
    app.add_node(inline_flag, html=(visit_inline_flag, depart_flag))
    app.add_node(flag, html=(visit_flag, depart_flag))
    app.add_role("inline-flag", inline_flag_role)
    app.connect("autodoc-process-docstring", process_docstring)
    # Connect to env-updated event which happens after reading all docs and before writing
    app.connect("env-updated", fix_inventory_uris)
    # app.connect("doctree-resolved", substitute_deprecated_text)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
