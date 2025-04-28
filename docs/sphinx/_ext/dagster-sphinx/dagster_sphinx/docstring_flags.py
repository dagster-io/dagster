import re
from typing import Union

import dagster._check as check
import docutils.nodes as nodes
from dagster._annotations import BetaInfo, DeprecatedInfo, PreviewInfo, SupersededInfo
from sphinx.util.docutils import SphinxDirective

# ########################
# ##### AUTODOC
# ########################

# Below APIs are called during docstring processing.


def inject_object_flag(
    obj: object,
    info: Union[SupersededInfo, DeprecatedInfo, PreviewInfo, BetaInfo],
    docstring: list[str],
) -> None:
    if isinstance(info, DeprecatedInfo):
        additional_text = f" {info.additional_warn_text}." if info.additional_warn_text else ""
        flag_type = "deprecated"
        message = f"This API will be removed in version {info.breaking_version}.\n{additional_text}"
    elif isinstance(info, SupersededInfo):
        additional_text = f" {info.additional_warn_text}." if info.additional_warn_text else ""
        flag_type = "superseded"
        message = f"This API has been superseded.\n{additional_text}"
    elif isinstance(info, PreviewInfo):
        additional_text = f" {info.additional_warn_text}." if info.additional_warn_text else ""
        flag_type = "preview"
        message = (
            f"This API is currently in preview, and may have breaking changes in patch version releases. "
            f"This API is not considered ready for production use.\n{additional_text}"
        )
    elif isinstance(info, BetaInfo):
        additional_text = f" {info.additional_warn_text}." if info.additional_warn_text else ""
        flag_type = "beta"
        message = (
            f"This API is currently in beta, and may have breaking changes in minor version releases, "
            f"with behavior changes in patch releases.\n{additional_text}"
        )
    else:
        check.failed(f"Unexpected info type {type(info)}")
    for line in reversed([f".. flag:: {flag_type}", "", f"   {message}", ""]):
        docstring.insert(0, line)


def inject_param_flag(
    lines: list[str],
    param: str,
    info: Union[BetaInfo, DeprecatedInfo],
):
    if isinstance(info, DeprecatedInfo):
        flag = ":inline-flag:`deprecated`"
    elif isinstance(info, BetaInfo):
        flag = ":inline-flag:`beta`"
    else:
        check.failed(f"Unexpected info type {type(info)}")
    index = next((i for i in range(len(lines)) if re.search(f"^:param {param}", lines[i])), None)
    modified_line = (
        re.sub(rf"^:param {param}:", f":param {param}: {flag} ", lines[index])
        if index is not None
        else None
    )

    if index is not None and modified_line is not None:
        lines[index] = modified_line


# ########################
# ##### CUSTOM FLAGS
# ########################

# Below APIs are called during RST rendering.

FLAG_ATTRS = ("flag_type", "message")


def inline_flag_role(_name, _rawtext, text, _lineno, inliner, _options={}, _content=[]):
    flag_node = inline_flag(flag_type=text)
    return [flag_node], []


class inline_flag(nodes.Inline, nodes.TextElement):
    local_attributes = FLAG_ATTRS


def visit_inline_flag(self, node: inline_flag):
    flag_type = node.attributes["flag_type"]
    # The "hidden" elements are not visible on screen, but are picked up by the search
    # crawler to provide better structure to search results.
    html = f"""
    <span class="flag {flag_type}">
      <span class="hidden">(</span>
      {flag_type}
      <span class="hidden">)</span>
    </span>
    """
    self.body.append(html)


class flag(nodes.Element):
    local_attributes = [*nodes.Element.local_attributes, *FLAG_ATTRS]


def visit_flag(self, node: flag):
    flag_type, message = [node.attributes[k] for k in FLAG_ATTRS]
    # We are currently not parsing the content of the message, so manually sub
    # all `references` with `<cite>` tags, which is what the HTML writer does
    # for parsed RST.
    message = re.sub(r"`(\S+?)`", r"<cite>\1</cite>", message)
    header, *body = message.splitlines()
    processed_lines = [header, *(f"<p>{line}</>" for line in body)]
    message_html = "\n".join(processed_lines)
    # The "hidden" elements are not visible on screen, but are picked up by the search
    # crawler to provide better structure to search results.
    html = f"""
    <div class="flag">
      <p>
        <span class="flag {flag_type}">
          <span class="hidden">(</span>
          {flag_type}
          <span class="hidden">)</span>
        </span>
      </>
      {message_html}
    </div>
    """
    self.body.append(html)


def depart_flag(self, node: flag): ...


class FlagDirective(SphinxDirective):
    # Takes two arguments-- the first word is the flag type and the remaining words are the message.
    required_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        flag_node = flag()
        flag_node["flag_type"] = self.arguments[0]
        flag_node["message"] = " ".join(self.content)
        return [flag_node]
