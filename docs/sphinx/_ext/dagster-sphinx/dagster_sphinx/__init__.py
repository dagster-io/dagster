from typing import List, Optional, Tuple, Type, TypeVar

import docutils.nodes as nodes
from dagster._annotations import (
    get_deprecated_info,
    get_deprecated_params,
    get_experimental_info,
    get_experimental_params,
    has_deprecated_params,
    has_experimental_params,
    is_deprecated,
    is_experimental,
    is_public,
)
from dagster._record import get_original_class, is_record
from typing_extensions import Literal, TypeAlias

from dagster_sphinx.configurable import ConfigurableDocumenter
from dagster_sphinx.docstring_flags import (
    FlagDirective,
    depart_flag,
    flag,
    inline_flag,
    inline_flag_role,
    visit_flag,
    visit_inline_flag,
)
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc import (
    ClassDocumenter,
    ObjectMember,
    Options as AutodocOptions,
)
from sphinx.util import logging

from .docstring_flags import inject_object_flag, inject_param_flag

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

    def get_object_members(self, want_all: bool) -> Tuple[bool, List[ObjectMember]]:
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
    lines: List[str],
) -> None:
    assert app.env is not None

    if is_deprecated(obj):
        inject_object_flag(obj, get_deprecated_info(obj), lines)

    if has_deprecated_params(obj):
        params = get_deprecated_params(obj)
        for param, info in params.items():
            inject_param_flag(lines, param, info)

    if is_experimental(obj):
        inject_object_flag(obj, get_experimental_info(obj), lines)

    if has_experimental_params(obj):
        params = get_experimental_params(obj)
        for param, info in params.items():
            inject_param_flag(lines, param, info)


T_Node = TypeVar("T_Node", bound=nodes.Node)


def get_child_as(node: nodes.Node, index: int, node_type: Type[T_Node]) -> T_Node:
    child = node.children[index]
    assert isinstance(
        child, node_type
    ), f"Docutils node not of expected type. Expected `{node_type}`, got `{type(child)}`."
    return child


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
    app.add_directive("flag", FlagDirective)
    app.add_node(inline_flag, html=(visit_inline_flag, depart_flag))
    app.add_node(flag, html=(visit_flag, depart_flag))
    app.add_role("inline-flag", inline_flag_role)
    app.connect("autodoc-process-docstring", process_docstring)
    # app.connect("doctree-resolved", substitute_deprecated_text)
    app.connect("build-finished", check_custom_errors)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
