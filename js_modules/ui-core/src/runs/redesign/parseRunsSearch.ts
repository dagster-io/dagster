import {
  AbstractParseTreeVisitor,
  CharStream,
  CommonTokenStream,
  ParseTree,
  ParserRuleContext,
} from 'antlr4ng';
import uniqBy from 'lodash/uniqBy';

import {
  RUNS_SEARCH_ATTRIBUTES,
  RunsSearchAttribute,
  TAG_KEY_BY_ATTRIBUTE,
  getAttributeForTagKey,
  isTagBackedAttribute,
} from './runsSearchAttributes';
import {RunStatus} from '../../graphql/types';
import {AntlrInputErrorListener} from '../../selection/AntlrInputErrorListener';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {getValueNodeValue} from '../../selection/SelectionInputUtil';
import {SelectionAutoCompleteLexer} from '../../selection/generated/SelectionAutoCompleteLexer';
import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  AttributeValueContext,
  CommaExpressionWrapper1Context,
  DigitsValueContext,
  DownTraversalExpressionContext,
  ExpressionlessFunctionExpressionContext,
  FunctionCallExpressionContext,
  IncompleteAndExpressionContext,
  IncompleteAttributeExpressionMissingSecondValueContext,
  IncompleteAttributeExpressionMissingValueContext,
  IncompleteExpressionContext,
  IncompleteNotExpressionContext,
  IncompleteOrExpressionContext,
  IncompletePlusTraversalExpressionContext,
  IncompletePlusTraversalExpressionMissingValueContext,
  NotExpressionContext,
  NullStringValueContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  QuotedStringValueContext,
  SelectionAutoCompleteParser,
  StartContext,
  TraversalAllowedExpressionContext,
  TraversalAllowedParenthesizedExpressionContext,
  UnclosedExpressionlessFunctionExpressionContext,
  UnclosedFunctionExpressionContext,
  UnmatchedValueContext,
  UnquotedStringValueContext,
  UpAndDownTraversalExpressionContext,
  UpTraversalExpressionContext,
} from '../../selection/generated/SelectionAutoCompleteParser';
import {SelectionAutoCompleteVisitor} from '../../selection/generated/SelectionAutoCompleteVisitor';
import {RunFilterToken, RunFilterTokenType} from '../RunsFilterUtils';

type TokenBackedAttribute =
  | 'id'
  | 'status'
  | 'job'
  | 'snapshot_id'
  | 'created_after'
  | 'created_before';

const TOKEN_TYPE_BY_ATTRIBUTE = {
  id: 'id',
  status: 'status',
  job: 'job',
  snapshot_id: 'snapshotId',
  created_after: 'created_date_after',
  created_before: 'created_date_before',
} as const satisfies Record<TokenBackedAttribute, RunFilterTokenType>;

// The server ORs values within these lists, so they are the only attributes `or` can combine.
const SET_ATTRIBUTE_CONFLICT_MESSAGES = {
  id: 'Use or to match any of several IDs',
  status: 'Use or to match any of several statuses',
} as const satisfies Record<'id' | 'status', string>;

const SINGLE_VALUE_MESSAGES = {
  job: 'Only one job per search',
  code_location: 'Only one code location per search',
  sensor: 'Only one sensor per search',
  schedule: 'Only one schedule per search',
  user: 'Only one user per search',
  backfill: 'Only one backfill per search',
  partition: 'Only one partition per search',
  tag: 'Only one value per tag key',
  snapshot_id: 'Only one snapshot ID per search',
  created_after: 'Only one created_after per search',
  created_before: 'Only one created_before per search',
} as const satisfies Record<Exclude<RunsSearchAttribute, 'id' | 'status'>, string>;

const OR_MESSAGE = 'or only combines IDs or statuses';
const TAG_FORMAT_MESSAGE = 'tag needs key=value, for example tag:team=data';
const BARE_VALUE_MESSAGE = 'Add an attribute, for example job:my_job';
const SYNTAX_MESSAGE = 'Check the search syntax, for example job:my_job and status:failure';
const INCOMPLETE_MESSAGE = 'Finish the search before applying it';
const NOT_MESSAGE = "not isn't supported in runs search";
const TRAVERSAL_MESSAGE = "Traversal (+) isn't supported in runs search";
const FUNCTION_MESSAGE = "Functions aren't supported in runs search";
const WILDCARD_MESSAGE = "Wildcards (*) aren't supported in runs search";

type ContextClass = new (...args: never[]) => ParserRuleContext;

// Expressions runs search rejects outright, and the message for each.
const UNSUPPORTED_EXPRESSION_MESSAGES = [
  [NotExpressionContext, NOT_MESSAGE],
  [IncompleteNotExpressionContext, NOT_MESSAGE],
  [IncompleteAndExpressionContext, 'Add a search term after and'],
  [IncompleteOrExpressionContext, 'Add a search term after or'],
  [UnmatchedValueContext, BARE_VALUE_MESSAGE],
  [AllExpressionContext, WILDCARD_MESSAGE],
  [UpTraversalExpressionContext, TRAVERSAL_MESSAGE],
  [DownTraversalExpressionContext, TRAVERSAL_MESSAGE],
  [UpAndDownTraversalExpressionContext, TRAVERSAL_MESSAGE],
  [IncompletePlusTraversalExpressionContext, TRAVERSAL_MESSAGE],
  [IncompletePlusTraversalExpressionMissingValueContext, TRAVERSAL_MESSAGE],
  [FunctionCallExpressionContext, FUNCTION_MESSAGE],
  [ExpressionlessFunctionExpressionContext, FUNCTION_MESSAGE],
  [UnclosedExpressionlessFunctionExpressionContext, FUNCTION_MESSAGE],
  [UnclosedFunctionExpressionContext, FUNCTION_MESSAGE],
  [IncompleteAttributeExpressionMissingSecondValueContext, TAG_FORMAT_MESSAGE],
] as const satisfies readonly (readonly [ContextClass, string])[];

const RUN_STATUSES: string[] = Object.values(RunStatus);
const TIMESTAMP_PATTERN = /^\d+(\.\d+)?$/;

type RunsSearchParseResult =
  | {
      tokens: RunFilterToken[];
      errors: [];
    }
  | {
      tokens: null;
      errors: SyntaxError[];
    };

type TermNode = {
  type: 'term';
  attribute: RunsSearchAttribute;
  // Terms sharing a conflict key filter the same server field or tag key.
  conflictKey: string;
  token: RunFilterToken;
  from: number;
  to: number;
};

type OperatorNode = {
  type: 'and' | 'or';
  operands: RunsSearchNode[];
  from: number;
  to: number;
};

type ErrorNode = {
  type: 'error';
  error: SyntaxError;
};

type RunsSearchNode = TermNode | OperatorNode | ErrorNode;

type ValueGroup = {
  attribute: RunsSearchAttribute;
  conflictKey: string;
  tokens: RunFilterToken[];
  from: number;
  to: number;
};

type ValueReadResult =
  | {
      value: string;
    }
  | {
      error: string;
    };

const isRunsSearchAttribute = (attribute: string): attribute is RunsSearchAttribute =>
  (RUNS_SEARCH_ATTRIBUTES as readonly string[]).includes(attribute);

const isSetAttribute = (attribute: RunsSearchAttribute): attribute is 'id' | 'status' =>
  attribute in SET_ATTRIBUTE_CONFLICT_MESSAGES;

const getTokenString = (token: RunFilterToken) => `${token.token}:${token.value}`;

const getContextRange = (ctx: ParserRuleContext) => {
  const from = ctx.start?.start ?? 0;
  return {
    from,
    to: from + ctx.getText().trimEnd().length,
  };
};

const createErrorNode = (message: string, ctx: ParserRuleContext): ErrorNode => ({
  type: 'error',
  error: {
    message,
    ...getContextRange(ctx),
  },
});

const readValue = (ctx: AttributeValueContext | null): ValueReadResult => {
  const valueCtx = ctx?.value() ?? null;

  if (valueCtx instanceof NullStringValueContext) {
    return {error: "<null> isn't supported in runs search"};
  }

  const isComplete =
    valueCtx instanceof QuotedStringValueContext ||
    valueCtx instanceof UnquotedStringValueContext ||
    valueCtx instanceof DigitsValueContext;
  if (!isComplete) {
    return {error: 'Close the quote around this value'};
  }

  const value = getValueNodeValue(valueCtx);
  // Quoted values are literal, so only an unquoted `*` is a wildcard.
  if (!(valueCtx instanceof QuotedStringValueContext) && value.includes('*')) {
    return {error: WILDCARD_MESSAGE};
  }

  return {value};
};

const getScalarValueError = (attribute: RunsSearchAttribute, value: string) => {
  if (value === '') {
    return `Add a value after ${attribute}:`;
  }

  if (attribute === 'status' && !RUN_STATUSES.includes(value.toUpperCase())) {
    return `Unknown status: ${value}`;
  }

  if (
    (attribute === 'created_after' || attribute === 'created_before') &&
    !TIMESTAMP_PATTERN.test(value)
  ) {
    return `${attribute} needs a Unix timestamp in seconds`;
  }

  // The legacy token format splits tag values at `=`, so they can't hold one.
  if (isTagBackedAttribute(attribute) && value.includes('=')) {
    return `${attribute} values can't contain =`;
  }

  return null;
};

const createTagTerm = (
  ctx: AttributeExpressionContext,
  key: string,
  value: string,
): RunsSearchNode => {
  if (key === '') {
    return createErrorNode(TAG_FORMAT_MESSAGE, ctx);
  }

  if (key.includes('=') || value.includes('=')) {
    return createErrorNode("Tag keys and values can't contain =", ctx);
  }

  return {
    type: 'term',
    attribute: getAttributeForTagKey(key) ?? 'tag',
    conflictKey: `tag:${key}`,
    token: {token: 'tag', value: `${key}=${value}`},
    ...getContextRange(ctx),
  };
};

const createScalarTerm = (
  ctx: AttributeExpressionContext,
  attribute: Exclude<RunsSearchAttribute, 'tag'>,
  value: string,
): RunsSearchNode => {
  const error = getScalarValueError(attribute, value);
  if (error) {
    return createErrorNode(error, ctx);
  }

  if (isTagBackedAttribute(attribute)) {
    const key = TAG_KEY_BY_ATTRIBUTE[attribute];
    return {
      type: 'term',
      attribute,
      conflictKey: `tag:${key}`,
      token: {token: 'tag', value: `${key}=${value}`},
      ...getContextRange(ctx),
    };
  }

  return {
    type: 'term',
    attribute,
    conflictKey: attribute,
    token: {
      token: TOKEN_TYPE_BY_ATTRIBUTE[attribute],
      value: attribute === 'status' ? value.toUpperCase() : value,
    },
    ...getContextRange(ctx),
  };
};

class RunsSearchVisitor
  extends AbstractParseTreeVisitor<RunsSearchNode>
  implements SelectionAutoCompleteVisitor<RunsSearchNode>
{
  // Incomplete expressions parse without a syntax error, so anything not handled below must
  // reject the search rather than fall through to an empty filter.
  override visitChildren(node: ParseTree): RunsSearchNode {
    if (node instanceof ParserRuleContext) {
      const message =
        UNSUPPORTED_EXPRESSION_MESSAGES.find(([Context]) => node instanceof Context)?.[1] ??
        INCOMPLETE_MESSAGE;
      return createErrorNode(message, node);
    }
    return {type: 'error', error: {message: INCOMPLETE_MESSAGE, from: 0, to: 0}};
  }

  private visitNode(ctx: ParserRuleContext | null, parent: ParserRuleContext) {
    return ctx ? (this.visit(ctx) ?? this.visitChildren(ctx)) : this.visitChildren(parent);
  }

  private visitOperator(
    type: OperatorNode['type'],
    ctx: AndExpressionContext | OrExpressionContext | CommaExpressionWrapper1Context,
  ): OperatorNode {
    return {
      type,
      operands: [this.visitNode(ctx.expr(0), ctx), this.visitNode(ctx.expr(1), ctx)],
      ...getContextRange(ctx),
    };
  }

  visitStart(ctx: StartContext) {
    return this.visitNode(ctx.expr(), ctx);
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visitNode(ctx.traversalAllowedExpr(), ctx);
  }

  visitTraversalAllowedParenthesizedExpression(
    ctx: TraversalAllowedParenthesizedExpressionContext,
  ) {
    return this.visitNode(ctx.parenthesizedExpr(), ctx);
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    return this.visitNode(ctx.expr(), ctx);
  }

  visitIncompleteExpression(ctx: IncompleteExpressionContext) {
    return this.visitNode(ctx.incompleteExpr(), ctx);
  }

  visitAndExpression(ctx: AndExpressionContext) {
    return this.visitOperator('and', ctx);
  }

  visitOrExpression(ctx: OrExpressionContext) {
    return this.visitOperator('or', ctx);
  }

  visitCommaExpressionWrapper1(ctx: CommaExpressionWrapper1Context) {
    return this.visitOperator('or', ctx);
  }

  visitIncompleteAttributeExpressionMissingValue(
    ctx: IncompleteAttributeExpressionMissingValueContext,
  ) {
    const attribute = ctx.attributeName().getText();
    if (attribute === 'tag') {
      return createErrorNode(TAG_FORMAT_MESSAGE, ctx);
    }
    return createErrorNode(`Add a value after ${attribute}:`, ctx);
  }

  visitAttributeExpression(ctx: AttributeExpressionContext): RunsSearchNode {
    const attribute = ctx.attributeName().getText();
    const first = readValue(ctx.attributeValue(0));
    const second = ctx.EQUAL() ? readValue(ctx.attributeValue(1)) : null;

    if (!isRunsSearchAttribute(attribute)) {
      return createErrorNode(`Unsupported attribute: "${attribute}"`, ctx);
    }

    if ('error' in first) {
      return createErrorNode(first.error, ctx);
    }

    if (second && 'error' in second) {
      return createErrorNode(second.error, ctx);
    }

    if (attribute === 'tag') {
      return second
        ? createTagTerm(ctx, first.value, second.value)
        : createErrorNode(TAG_FORMAT_MESSAGE, ctx);
    }

    if (second) {
      return createErrorNode('Only tag takes key=value, for example tag:team=data', ctx);
    }

    return createScalarTerm(ctx, attribute, first.value);
  }
}

const collectNodeErrors = (node: RunsSearchNode): SyntaxError[] => {
  if (node.type === 'error') {
    return [node.error];
  }

  if (node.type === 'term') {
    return [];
  }

  return node.operands.flatMap(collectNodeErrors);
};

const flattenOperands = (node: RunsSearchNode, type: OperatorNode['type']): RunsSearchNode[] =>
  node.type === type ? node.operands.flatMap((operand) => flattenOperands(operand, type)) : [node];

const createValueGroup = (node: RunsSearchNode): ValueGroup | SyntaxError => {
  if (node.type === 'term') {
    return {
      attribute: node.attribute,
      conflictKey: node.conflictKey,
      tokens: [node.token],
      from: node.from,
      to: node.to,
    };
  }

  if (node.type === 'error') {
    return node.error;
  }

  const range = {
    from: node.from,
    to: node.to,
  };

  if (node.type === 'and') {
    return {message: OR_MESSAGE, ...range};
  }

  const operands = flattenOperands(node, 'or');
  const terms = operands.filter((operand) => operand.type === 'term');
  const attributes = new Set(terms.map((term) => term.attribute));
  const [attribute] = [...attributes];

  if (terms.length !== operands.length || !attribute || attributes.size > 1) {
    return {message: OR_MESSAGE, ...range};
  }

  if (!isSetAttribute(attribute)) {
    return {message: SINGLE_VALUE_MESSAGES[attribute], ...range};
  }

  return {
    attribute,
    conflictKey: attribute,
    tokens: uniqBy(
      terms.map((term) => term.token),
      getTokenString,
    ),
    ...range,
  };
};

const getGroupSignature = (group: ValueGroup) => group.tokens.map(getTokenString).sort().join('\n');

const getConflictError = (group: ValueGroup, groups: ValueGroup[]): SyntaxError | null => {
  const firstMatch = groups.find((other) => other.conflictKey === group.conflictKey);
  if (
    !firstMatch ||
    firstMatch === group ||
    getGroupSignature(firstMatch) === getGroupSignature(group)
  ) {
    return null;
  }

  const message = isSetAttribute(group.attribute)
    ? SET_ATTRIBUTE_CONFLICT_MESSAGES[group.attribute]
    : SINGLE_VALUE_MESSAGES[group.attribute];
  return {
    message,
    from: group.from,
    to: group.to,
  };
};

const getTokensForTree = (root: RunsSearchNode): RunsSearchParseResult => {
  const nodeErrors = collectNodeErrors(root);
  if (nodeErrors.length) {
    return {tokens: null, errors: nodeErrors};
  }

  const groupsOrErrors = flattenOperands(root, 'and').map(createValueGroup);
  const groups = groupsOrErrors.filter((group): group is ValueGroup => 'conflictKey' in group);
  const groupErrors = groupsOrErrors.filter((group): group is SyntaxError => 'message' in group);
  const conflictErrors = groups
    .map((group) => getConflictError(group, groups))
    .filter((error): error is SyntaxError => error !== null);
  const errors = [...groupErrors, ...conflictErrors];

  if (errors.length) {
    return {tokens: null, errors};
  }

  // Emit in the rendering order so that parsing rendered text is a fixed point.
  const tokens = RUNS_SEARCH_ATTRIBUTES.flatMap((attribute) =>
    groups.filter((group) => group.attribute === attribute).flatMap((group) => group.tokens),
  );
  return {tokens: uniqBy(tokens, getTokenString), errors: []};
};

/**
 * Parses runs search text into legacy `q[]` filter tokens.
 *
 * - Empty text is `[]` (no filter); any rejected search is `tokens: null`, never `[]`.
 * - Attributes come out in a canonical order; IDs and statuses keep the order they were typed in.
 */
export const parseRunsSearch = (text: string): RunsSearchParseResult => {
  if (text.trim() === '') {
    return {tokens: [], errors: []};
  }

  let tree: StartContext;
  try {
    const lexer = new SelectionAutoCompleteLexer(CharStream.fromString(text));
    lexer.removeErrorListeners();
    lexer.addErrorListener(new AntlrInputErrorListener());

    const tokenStream = new CommonTokenStream(lexer);
    tokenStream.fill();

    const parser = new SelectionAutoCompleteParser(tokenStream);
    parser.removeErrorListeners();
    parser.addErrorListener(new AntlrInputErrorListener());

    tree = parser.start();
  } catch {
    return {tokens: null, errors: [{message: SYNTAX_MESSAGE, from: 0, to: text.length}]};
  }

  const visitor = new RunsSearchVisitor();
  return getTokensForTree(visitor.visit(tree) ?? visitor.visitChildren(tree));
};
