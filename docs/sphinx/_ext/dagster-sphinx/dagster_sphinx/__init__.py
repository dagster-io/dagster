from typing import List, Optional, Tuple, Type, TypeVar

import docutils.nodes as nodes
from dagster._annotations import is_deprecated, is_public
from sphinx.addnodes import versionmodified
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc import (
    ClassDocumenter,
    ObjectMembers,
    Options as AutodocOptions,
)
from sphinx.util import logging
from typing_extensions import Literal, TypeAlias

from dagster_sphinx.configurable import ConfigurableDocumenter

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


def record_error(env: BuildEnvironment, message: str) -> None:
    """Record an error in the Sphinx build environment. The error list is
    globally available during the build.
    """
    logger.info(message)
    if not hasattr(env, "dagster_errors"):
        setattr(env, "dagster_errors", [])
    getattr(env, "dagster_errors").append(message)


# ########################
# ##### CHECKS
# ########################


def check_public_method_has_docstring(env: BuildEnvironment, name: str, obj: object) -> None:
    if name != "__init__" and not obj.__doc__:
        message = (
            f"Docstring not found for {object.__name__}.{name}. "
            "All public methods and properties must have docstrings."
        )
        record_error(env, message)


class DagsterClassDocumenter(ClassDocumenter):
    """Overrides the default autodoc ClassDocumenter to adds some extra options."""

    objtype = "class"

    def get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]:
        _, unfiltered_members = super().get_object_members(want_all)
        # Use form `is_public(self.object, attr_name) if possible, because to access a descriptor
        # object (returned by e.g. `@staticmethod`) you need to go in through
        # `self.object.__dict__`-- the value provided in the member list is _not_ the descriptor!
        filtered_members = [
            m
            for m in unfiltered_members
            if m[0] in self.object.__dict__ and is_public(self.object.__dict__[m[0]])
        ]
        for member in filtered_members:
            check_public_method_has_docstring(self.env, member[0], member[1])
        return False, filtered_members


# This is a hook that will be executed for every processed docstring. It modifies the lines of the
# docstring in place.
def process_docstring(
    app: Sphinx,
    what: AutodocObjectType,
    name: str,
    obj: object,
    options: AutodocOptions,
    lines: List[str],
) -> None:
    assert app.env is not None

    # Insert a "deprecated" sphinx directive (this is built-in to autodoc) for objects flagged with
    # @deprecated.
    if is_deprecated(obj):
        # Note that these are in reversed order from how they will appear because we insert at the
        # front. We insert the <placeholder> string because the directive requires an argument that
        # we can't supply (we would have to know the version at which the object was deprecated).
        # We discard the "<placeholder>" string in `substitute_deprecated_text`.
        for line in ["", ".. deprecated:: <placeholder>"]:
            lines.insert(0, line)


T_Node = TypeVar("T_Node", bound=nodes.Node)


def get_child_as(node: nodes.Node, index: int, node_type: Type[T_Node]) -> T_Node:
    child = node.children[index]
    assert isinstance(
        child, node_type
    ), f"Docutils node not of expected type. Expected `{node_type}`, got `{type(child)}`."
    return child


def substitute_deprecated_text(app: Sphinx, doctree: nodes.Element, docname: str) -> None:
    # The `.. deprecated::` directive is rendered as a `versionmodified` node.
    # Find them all and replace the auto-generated text, which requires a version argument, with a
    # plain string "Deprecated".
    for node in doctree.findall(versionmodified):
        paragraph = get_child_as(node, 0, nodes.paragraph)
        inline = get_child_as(paragraph, 0, nodes.inline)
        text = get_child_as(inline, 0, nodes.Text)
        inline.replace(text, nodes.Text("Deprecated"))


def check_custom_errors(app: Sphinx, exc: Optional[Exception] = None) -> None:
    dagster_errors = getattr(app.env, "dagster_errors", [])
    if len(dagster_errors) > 0:
        for error_msg in dagster_errors:
            logger.info(error_msg)
        raise Exception(
            f"Bulid failed. Found {len(dagster_errors)} violations of docstring requirements."
        )


def setup(app):
    app.setup_extension("sphinx.ext.autodoc")  # Require autodoc extension
    app.add_autodocumenter(ConfigurableDocumenter)
    # override allows `.. autoclass::` to invoke DagsterClassDocumenter instead of default
    app.add_autodocumenter(DagsterClassDocumenter, override=True)
    app.connect("autodoc-process-docstring", process_docstring)
    app.connect("doctree-resolved", substitute_deprecated_text)
    app.connect("build-finished", check_custom_errors)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
