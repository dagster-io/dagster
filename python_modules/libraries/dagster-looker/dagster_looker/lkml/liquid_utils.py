import logging
import sys

from liquid import Environment
from liquid.ast import Node
from liquid.builtin.literal import LiteralNode, Token
from liquid.parse import expect, get_parser
from liquid.stream import TokenStream
from liquid.tag import Tag
from liquid.token import TOKEN_EOF, TOKEN_TAG

TAG_CONDITION = sys.intern("condition")
TAG_ENDCONDITION = sys.intern("endcondition")

TAG_PARAMETER = sys.intern("parameter")

logger = logging.getLogger("dagster_looker")


class ConditionTag(Tag):
    """Defines a custom Liquid tag to match Looker's condition tag,
    treats the condition as always true when rendering the output SQL.
    https://jg-rp.github.io/liquid/guides/custom-tags#add-a-tag.
    """

    name = TAG_CONDITION
    end = TAG_ENDCONDITION

    def __init__(self, env: Environment):
        super().__init__(env)
        self.parser = get_parser(self.env)

    def parse(self, stream: TokenStream) -> Node:
        expect(stream, TOKEN_TAG, value=TAG_CONDITION)
        stream.next_token()  # Skip open condition tag
        stream.next_token()  # Skip condition filter name

        block = self.parser.parse_block(stream, (TAG_ENDCONDITION, TOKEN_EOF))
        expect(stream, TOKEN_TAG, value=TAG_ENDCONDITION)
        return block


TAG_DATE_START = sys.intern("date_start")
TAG_DATE_END = sys.intern("date_end")


class DateTag(Tag):
    def __init__(self, env: Environment):
        super().__init__(env)
        self.parser = get_parser(self.env)

    def parse(self, stream: TokenStream) -> Node:
        expect(stream, TOKEN_TAG, value=self.name)
        stream.next_token()
        return LiteralNode(tok=Token(1, "date", "'2021-01-01'"))


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
        if any(analysis.variables) or TAG_CONDITION in analysis.tags:
            logger.warn(
                f"SQL for view `{model_name}`"
                f" in file `{filename}`"
                " contains Liquid variables or conditions. Upstream dependencies are parsed as best-effort."
            )
        return template.render({})
    except SyntaxError:
        return sql
