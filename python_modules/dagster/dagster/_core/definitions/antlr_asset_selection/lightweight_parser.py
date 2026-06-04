"""Lightweight, dependency-free replacement for the antlr4-generated asset
selection parser.

Reproduces the behavior of ``AntlrAssetSelectionVisitor`` (a hand-written
tokenizer + recursive-descent parser) so that ``antlr4-python3-runtime`` is no
longer a required dependency. The grammar mirrors ``AssetSelection.g4``:

    expr        : or_expr
    or_expr     : and_expr (OR and_expr)*
    and_expr    : not_expr (AND not_expr)*
    not_expr    : NOT not_expr | traversal | STAR
    traversal   : (DIGITS? PLUS)? atom (PLUS DIGITS?)?
    atom        : attributeExpr
                | functionName LPAREN expr RPAREN
                | LPAREN expr RPAREN

Precedence follows antlr's alternative ordering: atoms/traversals bind tightest,
then NOT, then AND, then OR. Traversals apply only to atoms/parens/function
calls (``traversalAllowedExpr``), never to STAR/NOT/AND/OR expressions.
"""

import re

from dagster._core.definitions.asset_selection import (
    AssetSelection,
    AutomationTypeAssetSelection,
    ChangedInBranchAssetSelection,
    CodeLocationAssetSelection,
    ColumnAssetSelection,
    ColumnTagAssetSelection,
    JobAssetSelection,
    KeyWildCardAssetSelection,
    PartitionsAssetSelection,
    ScheduleNameAssetSelection,
    SensorNameAssetSelection,
    StatusAssetSelection,
    TableNameAssetSelection,
)

# Attribute keywords that take a `keyword:value` form.
_ATTRIBUTES = {
    "key",
    "owner",
    "group",
    "tag",
    "kind",
    "code_location",
    "status",
    "column",
    "table_name",
    "column_tag",
    "changed_in_branch",
    "partitions",
    "automation_type",
    "sensor",
    "schedule",
    "job",
}
_FUNCTIONS = {"sinks", "roots"}
# Keyword tokens that are also valid as bare values (per grammar `value` rule).
_VALUE_KEYWORDS = {"sensor", "schedule", "job"}


class AssetSelectionSyntaxError(Exception):
    pass


# --- Tokenizer ---------------------------------------------------------------

# Order matters: longer/more-specific patterns first.
_TOKEN_SPEC = [
    ("WS", r"[ \t\r\n]+"),
    ("QUOTED_STRING", r'"[^"\\\r\n]*"'),
    ("NULL_STRING", r"<null>"),
    ("DIGITS", r"[0-9]+"),
    ("STAR", r"\*"),
    ("PLUS", r"\+"),
    ("COLON", r":"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("EQUAL", r"="),
    # wildcard string may contain '*'; covers UNQUOTED_STRING too.
    ("WILDCARD_STRING", r"[a-zA-Z_*][a-zA-Z0-9_*/]*"),
]
_TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pat})" for name, pat in _TOKEN_SPEC))


class _Token:
    __slots__ = ("kind", "pos", "text")

    def __init__(self, kind: str, text: str, pos: int):
        self.kind = kind
        self.text = text
        self.pos = pos

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.text!r})"


def _tokenize(s: str):
    tokens = []
    pos = 0
    while pos < len(s):
        m = _TOKEN_RE.match(s, pos)
        if not m:
            raise AssetSelectionSyntaxError(f"Unexpected character at position {pos}: {s[pos]!r}")
        kind = m.lastgroup
        text = m.group()
        pos = m.end()
        if kind == "WS":
            continue
        tokens.append(_Token(kind, text, m.start()))
    tokens.append(_Token("EOF", "", pos))
    return tokens


# --- Parser ------------------------------------------------------------------


class _Parser:
    def __init__(self, tokens, include_sources: bool):
        self._tokens = tokens
        self._i = 0
        self.include_sources = include_sources

    @property
    def _cur(self) -> _Token:
        return self._tokens[self._i]

    def _advance(self) -> _Token:
        tok = self._tokens[self._i]
        self._i += 1
        return tok

    def _expect(self, kind: str) -> _Token:
        if self._cur.kind != kind:
            raise AssetSelectionSyntaxError(
                f"Expected {kind} but got {self._cur.kind} ({self._cur.text!r})"
            )
        return self._advance()

    def _is_keyword(self, *words: str) -> bool:
        return self._cur.kind == "WILDCARD_STRING" and self._cur.text in words

    def parse(self) -> AssetSelection:
        result = self._parse_or()
        self._expect("EOF")
        return result

    def _parse_or(self) -> AssetSelection:
        left = self._parse_and()
        while self._is_keyword("or", "OR"):
            self._advance()
            right = self._parse_and()
            left = left | right
        return left

    def _parse_and(self) -> AssetSelection:
        left = self._parse_not()
        while self._is_keyword("and", "AND"):
            self._advance()
            right = self._parse_not()
            left = left & right
        return left

    def _parse_not(self) -> AssetSelection:
        if self._is_keyword("not", "NOT"):
            self._advance()
            selection = self._parse_not()
            return AssetSelection.all(include_sources=self.include_sources) - selection
        if self._cur.kind == "STAR":
            self._advance()
            return AssetSelection.all(include_sources=self.include_sources)
        return self._parse_traversal()

    def _parse_traversal(self) -> AssetSelection:
        # up traversal: DIGITS? PLUS
        up_depth = None
        has_up = False
        if self._cur.kind == "DIGITS" and self._tokens[self._i + 1].kind == "PLUS":
            up_depth = int(self._advance().text)
            self._expect("PLUS")
            has_up = True
        elif self._cur.kind == "PLUS":
            self._advance()
            has_up = True

        selection = self._parse_atom()

        # down traversal: PLUS DIGITS?
        has_down = False
        down_depth = None
        if self._cur.kind == "PLUS":
            self._advance()
            has_down = True
            if self._cur.kind == "DIGITS":
                down_depth = int(self._advance().text)

        if has_up and has_down:
            return selection.upstream(depth=up_depth) | selection.downstream(depth=down_depth)
        if has_up:
            return selection.upstream(depth=up_depth)
        if has_down:
            return selection.downstream(depth=down_depth)
        return selection

    def _parse_atom(self) -> AssetSelection:
        # function call: sinks(...) / roots(...)
        if self._is_keyword(*_FUNCTIONS) and self._tokens[self._i + 1].kind == "LPAREN":
            func = self._advance().text
            self._expect("LPAREN")
            inner = self._parse_or()
            self._expect("RPAREN")
            return inner.sinks() if func == "sinks" else inner.roots()

        # parenthesized
        if self._cur.kind == "LPAREN":
            self._advance()
            inner = self._parse_or()
            self._expect("RPAREN")
            return inner

        return self._parse_attribute()

    # --- value helpers -------------------------------------------------------

    def _read_key_value(self):
        """keyValue: QUOTED_STRING | UNQUOTED_STRING | UNQUOTED_WILDCARD_STRING."""
        tok = self._cur
        if tok.kind == "QUOTED_STRING":
            self._advance()
            return tok.text.strip('"')
        if tok.kind == "WILDCARD_STRING":
            self._advance()
            return tok.text
        raise AssetSelectionSyntaxError(f"Expected key value but got {tok.kind} ({tok.text!r})")

    def _read_value(self):
        """value: NULL_STRING | QUOTED_STRING | UNQUOTED_STRING | SENSOR|SCHEDULE|JOB."""
        tok = self._cur
        if tok.kind == "QUOTED_STRING":
            self._advance()
            return tok.text.strip('"')
        if tok.kind == "NULL_STRING":
            self._advance()
            return None
        if tok.kind == "WILDCARD_STRING":
            # UNQUOTED_STRING is [a-zA-Z_][a-zA-Z0-9_/]* (no '*'); keyword values allowed.
            self._advance()
            return tok.text
        raise AssetSelectionSyntaxError(f"Expected value but got {tok.kind} ({tok.text!r})")

    def _parse_attribute(self) -> AssetSelection:
        if self._cur.kind != "WILDCARD_STRING" or self._cur.text not in _ATTRIBUTES:
            raise AssetSelectionSyntaxError(
                f"Expected attribute keyword but got {self._cur.kind} ({self._cur.text!r})"
            )
        attr = self._advance().text
        self._expect("COLON")

        if attr == "key":
            return KeyWildCardAssetSelection(selected_key_wildcard=self._read_key_value())
        if attr == "tag":
            key = self._read_value()
            value = self._read_value() if self._maybe_equal() else None
            return AssetSelection.tag(key, value or "", include_sources=self.include_sources)
        if attr == "owner":
            return AssetSelection.owner(self._read_value())
        if attr == "group":
            group = self._read_value()
            return AssetSelection.groups(
                *([] if not group else [group]), include_sources=self.include_sources
            )
        if attr == "kind":
            return AssetSelection.kind(self._read_value(), include_sources=self.include_sources)
        if attr == "code_location":
            return CodeLocationAssetSelection(selected_code_location=self._read_value())
        if attr == "status":
            return StatusAssetSelection(selected_status=self._read_value())
        if attr == "column":
            return ColumnAssetSelection(selected_column=self._read_value())
        if attr == "table_name":
            return TableNameAssetSelection(selected_table_name=self._read_value())
        if attr == "column_tag":
            key = self._read_value()
            value = self._read_value() if self._maybe_equal() else None
            return ColumnTagAssetSelection(key=key, value=value or "")
        if attr == "changed_in_branch":
            return ChangedInBranchAssetSelection(selected_changed_in_branch=self._read_value())
        if attr == "partitions":
            return PartitionsAssetSelection(selected_partitions=self._read_value())
        if attr == "automation_type":
            return AutomationTypeAssetSelection(selected_automation_type=self._read_value())
        if attr == "sensor":
            return SensorNameAssetSelection(selected_sensor=self._read_value())
        if attr == "schedule":
            return ScheduleNameAssetSelection(selected_schedule=self._read_value())
        if attr == "job":
            return JobAssetSelection(selected_job=self._read_value())
        raise AssetSelectionSyntaxError(f"Unhandled attribute {attr!r}")  # pragma: no cover

    def _maybe_equal(self) -> bool:
        if self._cur.kind == "EQUAL":
            self._advance()
            return True
        return False


class LightweightAssetSelectionParser:
    """Drop-in replacement for ``AntlrAssetSelectionParser``."""

    def __init__(self, selection_str: str, include_sources: bool = False):
        tokens = _tokenize(selection_str)
        self._asset_selection = _Parser(tokens, include_sources).parse()

    @property
    def asset_selection(self) -> AssetSelection:
        return self._asset_selection
