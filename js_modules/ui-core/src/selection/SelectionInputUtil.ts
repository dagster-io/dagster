import {ParserRuleContext} from 'antlr4ng';

import {
  AttributeValueContext,
  DigitsValueContext,
  IncompleteLeftQuotedStringValueContext,
  IncompleteRightQuotedStringValueContext,
  QuotedStringValueContext,
  UnclosedExpressionlessFunctionExpressionContext,
  UnclosedFunctionExpressionContext,
  UnclosedParenthesizedExpressionContext,
  UnquotedRejectedValueContext,
  UnquotedStringValueContext,
} from './generated/SelectionAutoCompleteParser';

/** Unicode "other" and separator characters: drop them from an unquoted value, don't quote them. */
const HIDDEN_CHARACTER_PATTERN = /[\p{C}\p{Z}]/u;

type UnquotedValueProblem =
  | {type: 'hidden-character'; character: string}
  | {type: 'backslash'}
  | {type: 'wildcard'};

/** The first thing in an unquoted value that quoting can't safely fix, if any. */
export function getUnquotedValueProblem(text: string): UnquotedValueProblem | null {
  const hiddenCharacter = HIDDEN_CHARACTER_PATTERN.exec(text)?.[0];
  if (hiddenCharacter) {
    return {type: 'hidden-character', character: hiddenCharacter};
  }
  if (text.includes('\\')) {
    return {type: 'backslash'};
  }
  // Quoting makes a `*` literal, which changes the search wherever it would be a wildcard.
  if (text.includes('*')) {
    return {type: 'wildcard'};
  }
  return null;
}

/** Attributes that take a key=value pair. */
export const KEY_VALUE_ATTRIBUTES = ['tag', 'column_tag'] as const;

export const removeQuotesFromString = (value: string) => {
  if (value.length > 1 && value[0] === '"' && value[value.length - 1] === '"') {
    return value.slice(1, -1);
  }
  return value;
};

export function getValueNodeValue(ctx: ParserRuleContext | null) {
  if (
    ctx instanceof DigitsValueContext ||
    ctx instanceof UnquotedStringValueContext ||
    ctx instanceof UnquotedRejectedValueContext
  ) {
    return ctx.getText();
  }
  if (ctx instanceof IncompleteLeftQuotedStringValueContext) {
    return ctx.getText().slice(1);
  }
  if (ctx instanceof IncompleteRightQuotedStringValueContext) {
    return ctx.getText().slice(0, -1);
  }
  if (ctx instanceof QuotedStringValueContext) {
    return ctx.getText().slice(1, -1);
  }
  if (ctx instanceof AttributeValueContext) {
    return getValueNodeValue(ctx.value());
  }
  return ctx?.getText() ?? '';
}

export function isInsideExpressionlessParenthesizedExpression(
  context: ParserRuleContext | undefined,
) {
  const parent = context?.parent;
  if (parent) {
    if (parent instanceof UnclosedParenthesizedExpressionContext) {
      return true;
    }
    if (parent instanceof UnclosedFunctionExpressionContext) {
      return true;
    }
    if (parent instanceof UnclosedExpressionlessFunctionExpressionContext) {
      return true;
    }
    return isInsideExpressionlessParenthesizedExpression(parent);
  }
  return false;
}
