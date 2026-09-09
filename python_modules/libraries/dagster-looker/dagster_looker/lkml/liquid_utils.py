import logging
import sys
from collections.abc import Iterable
from typing import TextIO

from liquid import Environment
from liquid.ast import BlockNode, Node
from liquid.builtin.content import ContentNode
from liquid.context import RenderContext
from liquid.exceptions import LiquidError
from liquid.parser import get_parser
from liquid.stream import TokenStream
from liquid.tag import Tag
from liquid.token import TOKEN_EOF, TOKEN_EXPRESSION, TOKEN_TAG, Token

TAG_CONDITION = sys.intern("condition")
TAG_ENDCONDITION = sys.intern("endcondition")
END_CONDITION_BLOCK = frozenset((TAG_ENDCONDITION, TOKEN_EOF))

TAG_PARAMETER = sys.intern("parameter")

logger = logging.getLogger("dagster_looker")


def _skip_tag_expression(stream: TokenStream) -> None:
    """Skip the argument of a Looker tag (e.g. the filter name in `{% condition holiday %}`).

    Leaves the stream positioned on the last token of the tag, as the parser expects.
    """
    if stream.peek.kind == TOKEN_EXPRESSION:
        next(stream)


class ConditionNode(Node):
    """Renders the body of a Looker `condition` block unconditionally.

    A dedicated node (rather than the bare block) keeps the `condition` tag
    visible to template static analysis.
    """

    __slots__ = ("block",)

    def __init__(self, token: Token, block: BlockNode):
        super().__init__(token)
        self.block = block
        # Enclosing tags like `if` and `capture` discard blocks that are blank, so
        # this must reflect the body rather than defaulting to True.
        self.blank = block.blank

    def __str__(self) -> str:
        return f"{{% condition %}}{self.block}{{% endcondition %}}"

    def render_to_output(self, context: RenderContext, buffer: TextIO) -> int:
        return self.block.render(context, buffer)

    def children(
        self, static_context: RenderContext, *, include_partials: bool = True
    ) -> Iterable[Node]:
        yield self.block


class ConditionTag(Tag):
    """Defines a custom Liquid tag to match Looker's condition tag,
    treats the condition as always true when rendering the output SQL.
    https://jg-rp.github.io/liquid/guides/custom-tags#add-a-tag.
    """

    name = TAG_CONDITION
    end = TAG_ENDCONDITION

    def parse(self, stream: TokenStream) -> Node:
        token = stream.expect(TOKEN_TAG, value=TAG_CONDITION)
        _skip_tag_expression(stream)
        next(stream)
        block = get_parser(self.env).parse_block(stream, END_CONDITION_BLOCK)
        stream.expect(TOKEN_TAG, value=TAG_ENDCONDITION)
        return ConditionNode(token, block)


TAG_DATE_START = sys.intern("date_start")
TAG_DATE_END = sys.intern("date_end")


class DateTag(Tag):
    block = False

    def parse(self, stream: TokenStream) -> Node:
        token = stream.expect(TOKEN_TAG, value=self.name)
        _skip_tag_expression(stream)
        return ContentNode(token, "'2021-01-01'")


class DateStartTag(DateTag):
    name = TAG_DATE_START


class DateEndTag(DateTag):
    name = TAG_DATE_END


env = Environment()
env.add_tag(ConditionTag)
env.add_tag(DateStartTag)
env.add_tag(DateEndTag)


def best_effort_render_liquid_sql(model_name: str, filename: str, sql: str) -> str:
    """Looker supports the Liquid templating language in SQL queries. This function
    attempts to render the Liquid SQL query by naively rendering the template with
    an empty context.
    """
    try:
        template = env.from_string(sql)
        analysis = template.analyze()
        if analysis.variables or TAG_CONDITION in analysis.tags:
            logger.warning(
                f"SQL for view `{model_name}`"
                f" in file `{filename}`"
                " contains Liquid variables or conditions. Upstream dependencies are parsed as best-effort."
            )
        return template.render({})
    except LiquidError:
        return sql
